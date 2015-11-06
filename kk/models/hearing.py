from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from .base import BaseModel
from .comment import BaseComment
from .images import BaseImage


class Hearing(BaseModel):
    COMMENT_OPTION_DISALLOW = '1'
    COMMENT_OPTION_REGISTERED = '2'
    COMMENT_OPTION_ANONYMOUS = '3'

    COMMENT_OPTION = (
        (COMMENT_OPTION_DISALLOW, 'Disallow'),
        (COMMENT_OPTION_REGISTERED, 'Registered'),
        (COMMENT_OPTION_ANONYMOUS, 'Anonymous')
    )
    close_at = models.DateTimeField(verbose_name=_('Closing time'), default=timezone.now)
    n_comments = models.IntegerField(verbose_name=_('Number of comments'), blank=True, default=0)
    closed = models.BooleanField(verbose_name=_('Whether hearing is closed'), default=False)
    heading = models.TextField(verbose_name=_('Heading'), blank=True, default='')
    abstract = models.TextField(verbose_name=_('Abstract'), blank=True, default='')
    content = models.TextField(verbose_name=_('Content'), blank=True, default='')
    borough = models.CharField(verbose_name=_('Borough to which hearing concerns'), blank=True, default='', max_length=200)
    comment_option = models.CharField(verbose_name=_('Commenting option'), max_length=1, choices=COMMENT_OPTION, default='1')
    servicemap_url = models.CharField(verbose_name=_('Servicemap url'), default='', max_length=255, blank=True)
    latitude = models.CharField(verbose_name=_('Latitude'), max_length=20, default='', blank=True)
    longitude = models.CharField(verbose_name=_('Longitude'), max_length=20, default='', blank=True)
    labels = models.ManyToManyField("Label", blank=True)


class HearingImage(BaseImage):
    hearing = models.ForeignKey(Hearing, related_name="images")


class HearingComment(BaseComment):
    hearing = models.ForeignKey(Hearing, related_name="comments")
