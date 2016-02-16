from urllib.parse import urljoin

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html
from djgeojson.fields import GeometryField
from reversion import revisions

from democracy.models.comment import recache_on_save
from democracy.utils.hmac_hash import get_hmac_b64_encoded

from .base import Commentable, StringIdBaseModel
from .comment import BaseComment
from .images import BaseImage


class Hearing(Commentable, StringIdBaseModel):
    open_at = models.DateTimeField(verbose_name=_('opening time'), default=timezone.now)
    close_at = models.DateTimeField(verbose_name=_('closing time'), default=timezone.now)
    force_closed = models.BooleanField(verbose_name=_('force hearing closed'), default=False)
    title = models.CharField(verbose_name=_('title'), max_length=255)
    abstract = models.TextField(verbose_name=_('abstract'), blank=True, default='')
    borough = models.CharField(verbose_name=_('borough'), blank=True, default='', max_length=200)
    servicemap_url = models.CharField(verbose_name=_('service map URL'), default='', max_length=255, blank=True)
    geojson = GeometryField(blank=True, null=True, verbose_name=_('area'))

    labels = models.ManyToManyField("Label", verbose_name=_('labels'), blank=True)
    followers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name=_('followers'),
        help_text=_('users who follow this hearing'),
        related_name='followed_hearings', blank=True, editable=False
    )

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
        super().check_commenting(request)

    @property
    def preview_code(self):
        if not self.pk:
            return None
        return get_hmac_b64_encoded(self.pk)

    @property
    def preview_url(self):
        if not (self.preview_code and hasattr(settings, 'UI_BASE_URL')):
            return ''
        url = urljoin(settings.UI_BASE_URL, '/hearing/%s/?preview=%s' % (self.pk, self.preview_code))
        return format_html(
            '<a href="%s">%s</a>' % (url, url)
        )


class HearingImage(BaseImage):
    parent_field = "hearing"
    hearing = models.ForeignKey(Hearing, related_name="images")

    class Meta:
        verbose_name = _('hearing image')
        verbose_name_plural = _('hearing images')


@revisions.register
@recache_on_save
class HearingComment(BaseComment):
    parent_field = "hearing"
    parent_model = Hearing
    hearing = models.ForeignKey(Hearing, related_name="comments")

    class Meta:
        verbose_name = _('hearing comment')
        verbose_name_plural = _('hearing comments')
