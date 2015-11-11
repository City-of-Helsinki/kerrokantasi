from django.db import models
from django.db.models.signals import post_save
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

import reversion

from .base import BaseModel, WithCommentsMixin
from .comment import BaseComment
from .images import BaseImage


class Hearing(WithCommentsMixin, BaseModel):
    COMMENT_OPTION_DISALLOW = '1'
    COMMENT_OPTION_REGISTERED = '2'
    COMMENT_OPTION_ANONYMOUS = '3'

    COMMENT_OPTION = (
        (COMMENT_OPTION_DISALLOW, 'Disallow'),
        (COMMENT_OPTION_REGISTERED, 'Registered'),
        (COMMENT_OPTION_ANONYMOUS, 'Anonymous')
    )
    close_at = models.DateTimeField(verbose_name=_('Closing time'), default=timezone.now)
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

    def __str__(self):
        return self.heading


class HearingImage(BaseImage):
    hearing = models.ForeignKey(Hearing, related_name="images")


@reversion.register
class HearingComment(BaseComment):
    parent_field = "hearing"
    parent_model = Hearing
    hearing = models.ForeignKey(Hearing, related_name="comments")


def hearing_recache(sender, instance, using, **kwargs):
    # recache number of comments
    instance.hearing.recache_n_comments()
    # recache number of votes
    instance.recache_n_votes()

post_save.connect(hearing_recache, sender=HearingComment)
