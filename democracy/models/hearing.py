from urllib.parse import urljoin

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.contrib.gis.db import models
from django.db.models import Sum
from django.utils import timezone
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from djgeojson.fields import GeoJSONField
from autoslug import AutoSlugField
from autoslug.utils import generate_unique_slug
from parler.models import TranslatedFields, TranslatableModel
from parler.managers import TranslatableQuerySet

from democracy.enums import InitialSectionType
from democracy.utils.hmac_hash import get_hmac_b64_encoded
from democracy.utils.geo import get_geometry_from_geojson

from .base import BaseModelManager, StringIdBaseModel
from .organization import ContactPerson, Organization
from .project import ProjectPhase


class HearingQueryset(TranslatableQuerySet):
    def get_by_id_or_slug(self, id_or_slug):
        return self.get(models.Q(pk=id_or_slug) | models.Q(slug=id_or_slug))

    def filter_by_id_or_slug(self, id_or_slug):
        return self.filter(models.Q(pk=id_or_slug) | models.Q(slug=id_or_slug))


class Hearing(StringIdBaseModel, TranslatableModel):
    open_at = models.DateTimeField(verbose_name=_('opening time'), default=timezone.now)
    close_at = models.DateTimeField(verbose_name=_('closing time'), default=timezone.now)
    force_closed = models.BooleanField(verbose_name=_('force hearing closed'), default=False)
    translations = TranslatedFields(
        title=models.CharField(verbose_name=_('title'), max_length=255),
        borough=models.CharField(verbose_name=_('borough'), blank=True, default='', max_length=200),
    )
    servicemap_url = models.CharField(verbose_name=_('service map URL'), default='', max_length=255, blank=True)
    geojson = GeoJSONField(blank=True, null=True, verbose_name=_('area'))
    geometry = models.GeometryField(blank=True, null=True, verbose_name=_('area geometry'))
    organization = models.ForeignKey(
        Organization,
        verbose_name=_('organization'),
        related_name="hearings", blank=True, null=True, on_delete=models.PROTECT
    )
    labels = models.ManyToManyField("Label", verbose_name=_('labels'), blank=True)
    followers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name=_('followers'),
        help_text=_('users who follow this hearing'),
        related_name='followed_hearings', blank=True, editable=False
    )
    slug = AutoSlugField(verbose_name=_('slug'), populate_from='title', editable=True, unique=True, blank=True,
                         help_text=_('You may leave this empty to automatically generate a slug'))
    n_comments = models.IntegerField(verbose_name=_('number of comments'), blank=True, default=0, editable=False)
    contact_persons = models.ManyToManyField(ContactPerson, verbose_name=_('contact persons'), related_name='hearings')
    project_phase = models.ForeignKey(ProjectPhase, verbose_name=_('project phase'), related_name='hearings',
                                      on_delete=models.PROTECT, null=True, blank=True)

    objects = BaseModelManager.from_queryset(HearingQueryset)()
    original_manager = models.Manager()

    class Meta:
        verbose_name = _('hearing')
        verbose_name_plural = _('hearings')

    def __str__(self):
        return (self.title or self.id)

    @property
    def closed(self):
        return self.force_closed or not (self.open_at <= now() <= self.close_at)

    def check_commenting(self, request):
        if self.closed:
            raise ValidationError(_("%s is closed and does not allow comments anymore") % self, code="hearing_closed")

    def check_voting(self, request):
        if self.closed:
            raise ValidationError(_("%s is closed and does not allow voting anymore") % self, code="hearing_closed")

    @property
    def preview_code(self):
        if not self.pk:
            return None
        return get_hmac_b64_encoded(self.pk)

    @property
    def preview_url(self):
        if not (self.preview_code and hasattr(settings, 'DEMOCRACY_UI_BASE_URL')):
            return None
        url = urljoin(settings.DEMOCRACY_UI_BASE_URL, '/%s/?preview=%s' % (self.pk, self.preview_code))
        return url

    def save(self, *args, **kwargs):
        slug_field = self._meta.get_field('slug')

        # we need to manually use autoslug utils here with ModelManager, because automatic slug populating
        # uses our default manager, which can lead to a slug collision between this and a deleted hearing
        self.slug = generate_unique_slug(slug_field, self, self.slug, Hearing.original_manager)

        self.geometry = get_geometry_from_geojson(self.geojson)

        super().save(*args, **kwargs)

    def recache_n_comments(self):
        new_n_comments = (self.sections.all().aggregate(Sum('n_comments')).get('n_comments__sum') or 0)
        if new_n_comments != self.n_comments:
            self.n_comments = new_n_comments
            self.save(update_fields=("n_comments",))

    def get_main_section(self):
        try:
            return self.sections.get(type__identifier=InitialSectionType.MAIN)
        except ObjectDoesNotExist:
            return None

    def is_visible_for(self, user):
        if self.published and self.open_at < now():
            return True
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        user_organization = user.get_default_organization()
        if not (user_organization and self.organization):
            return False
        return self.organization in user.admin_organizations.all()

    def soft_delete(self, using=None):
        # we want deleted hearings to give way to new ones, the original slug from a deleted hearing
        # is now free to use
        self.slug += '-deleted'
        self.save()
        super().soft_delete(using=using)
