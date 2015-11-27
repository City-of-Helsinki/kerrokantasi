import reversion
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from jsonfield import JSONField

from kk.models.comment import recache_on_save

from .base import Commentable, StringIdBaseModel
from .comment import BaseComment
from .images import BaseImage


class Hearing(Commentable, StringIdBaseModel):
    open_at = models.DateTimeField(verbose_name=_('Opening time'), default=timezone.now)
    close_at = models.DateTimeField(verbose_name=_('Closing time'), default=timezone.now)
    force_closed = models.BooleanField(verbose_name=_('Whether hearing is closed'), default=False)
    title = models.CharField(verbose_name=_('Title'), max_length=255)
    abstract = models.TextField(verbose_name=_('Abstract'), blank=True, default='')
    borough = models.CharField(
        verbose_name=_('Borough to which hearing concerns'), blank=True, default='', max_length=200
    )
    servicemap_url = models.CharField(verbose_name=_('Service map URL'), default='', max_length=255, blank=True)
    latitude = models.FloatField(verbose_name=_('Latitude'), null=True)
    longitude = models.FloatField(verbose_name=_('Longitude'), null=True)
    geojson = JSONField(blank=True, null=True, verbose_name=_('GeoJSON object'), editable=False)
    labels = models.ManyToManyField("Label", blank=True)
    followers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, verbose_name=_('Users who follow'), related_name='followed_hearings', blank=True
    )

    def __str__(self):
        return self.title or self.id

    @property
    def closed(self):
        return self.force_closed or not (self.open_at <= now() <= self.close_at)

    def may_comment(self, request):
        if self.closed:
            raise ValidationError(_("%s is closed and does not allow comments anymore") % self, code="hearing_closed")
        return super().may_comment(request)


class HearingImage(BaseImage):
    parent_field = "hearing"
    hearing = models.ForeignKey(Hearing, related_name="images")


@reversion.register
@recache_on_save
class HearingComment(BaseComment):
    parent_field = "hearing"
    parent_model = Hearing
    hearing = models.ForeignKey(Hearing, related_name="comments")
