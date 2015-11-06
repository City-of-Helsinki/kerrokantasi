from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from .base import ModifiableModel


class Comment(ModifiableModel):
    content = models.TextField(verbose_name=_('Content'), blank=True, default='')
    votes = models.IntegerField(verbose_name=_('Votes given to this comment'), default=0)
    followers = models.ManyToManyField(settings.AUTH_USER_MODEL, verbose_name=_('Users who follow'), related_name='followers', blank=True)
    voters = models.ManyToManyField(settings.AUTH_USER_MODEL, verbose_name=_('Users who voted'), related_name='voters', blank=True)


class WithCommentMixin(models.Model):
    comments = models.ManyToManyField(Comment)

    class Meta:
        abstract = True
