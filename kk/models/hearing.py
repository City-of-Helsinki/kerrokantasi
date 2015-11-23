import reversion
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from kk.models.comment import recache_on_save

from .base import Commentable, StringIdBaseModel
from .comment import BaseComment
from .images import BaseImage


class Hearing(Commentable, StringIdBaseModel):
    open_at = models.DateTimeField(verbose_name=_('Opening time'), default=timezone.now)
    close_at = models.DateTimeField(verbose_name=_('Closing time'), default=timezone.now)
    closed = models.BooleanField(verbose_name=_('Whether hearing is closed'), default=False)
    title = models.CharField(verbose_name=_('Title'), max_length=255)
    abstract = models.TextField(verbose_name=_('Abstract'), blank=True, default='')
    borough = models.CharField(
        verbose_name=_('Borough to which hearing concerns'), blank=True, default='', max_length=200
    )
    servicemap_url = models.CharField(verbose_name=_('Servicemap url'), default='', max_length=255, blank=True)
    latitude = models.CharField(verbose_name=_('Latitude'), max_length=20, default='', blank=True)
    longitude = models.CharField(verbose_name=_('Longitude'), max_length=20, default='', blank=True)
    labels = models.ManyToManyField("Label", blank=True)
    followers = models.ManyToManyField(
        settings.AUTH_USER_MODEL, verbose_name=_('Users who follow'), related_name='followed_hearings', blank=True
    )

    def __str__(self):
        return self.title


class HearingImage(BaseImage):
    hearing = models.ForeignKey(Hearing, related_name="images")


@reversion.register
@recache_on_save
class HearingComment(BaseComment):
    parent_field = "hearing"
    parent_model = Hearing
    hearing = models.ForeignKey(Hearing, related_name="comments")
