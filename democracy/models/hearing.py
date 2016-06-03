from urllib.parse import urljoin

from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.utils.html import format_html
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from djgeojson.fields import GeometryField
from autoslug import AutoSlugField
from autoslug.utils import generate_unique_slug

from democracy.enums import InitialSectionType
from democracy.utils.hmac_hash import get_hmac_b64_encoded

from .base import BaseModelManager, StringIdBaseModel
from .organization import Organization


class HearingQueryset(models.QuerySet):
    def get_by_id_or_slug(self, id_or_slug):
        return self.get(models.Q(pk=id_or_slug) | models.Q(slug=id_or_slug))

    def filter_by_id_or_slug(self, id_or_slug):
        return self.filter(models.Q(pk=id_or_slug) | models.Q(slug=id_or_slug))


class Hearing(StringIdBaseModel):
    open_at = models.DateTimeField(verbose_name=_('opening time'), default=timezone.now)
    close_at = models.DateTimeField(verbose_name=_('closing time'), default=timezone.now)
    force_closed = models.BooleanField(verbose_name=_('force hearing closed'), default=False)
    title = models.CharField(verbose_name=_('title'), max_length=255)
    borough = models.CharField(verbose_name=_('borough'), blank=True, default='', max_length=200)
    servicemap_url = models.CharField(verbose_name=_('service map URL'), default='', max_length=255, blank=True)
    geojson = GeometryField(blank=True, null=True, verbose_name=_('area'))
    organization = models.ForeignKey(
        Organization,
        verbose_name=_('organization'),
        related_name="hearings", blank=True, null=True
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

    @property
    def preview_code(self):
        if not self.pk:
            return None
        return get_hmac_b64_encoded(self.pk)

    @property
    def preview_url(self):
        if not (self.preview_code and hasattr(settings, 'DEMOCRACY_UI_BASE_URL')):
            return ''
        url = urljoin(settings.DEMOCRACY_UI_BASE_URL, '/hearing/%s/?preview=%s' % (self.pk, self.preview_code))
        return format_html(
            '<a href="%s">%s</a>' % (url, url)
        )

    def save(self, *args, **kwargs):
        slug_field = self._meta.get_field('slug')

        # we need to manually use autoslug utils here with ModelManager, because automatic slug populating
        # uses our default manager, which can lead to a slug collision between this and a deleted hearing
        self.slug = generate_unique_slug(slug_field, self, self.slug, Hearing.original_manager)

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
