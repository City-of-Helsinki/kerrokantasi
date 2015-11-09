from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.db.models.signals import post_save

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

    def __str__(self):
        return self.heading

    def recache_n_comments(self):
        new_n_comments = self.comments.count()
        if new_n_comments != self.n_comments:
            self.n_comments = new_n_comments
            self.save(update_fields=("n_comments",))


class HearingImage(BaseImage):
    hearing = models.ForeignKey(Hearing, related_name="images")


class HearingComment(BaseComment):
    hearing = models.ForeignKey(Hearing, related_name="comments")


def hearing_n_comments_bump(sender, instance, using, **kwargs):
    instance.hearing.n_comments += 1
    instance.hearing.save()

post_save.connect(hearing_n_comments_bump, sender=HearingComment)
