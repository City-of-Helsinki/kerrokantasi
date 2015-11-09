from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from .base import BaseModel


class BaseComment(BaseModel):
    content = models.TextField(verbose_name=_('Content'), blank=True, default='')
    votes = models.IntegerField(verbose_name=_('Votes given to this comment'), default=0)
    followers = models.ManyToManyField(settings.AUTH_USER_MODEL, verbose_name=_('Users who follow'), related_name='+', blank=True)
    voters = models.ManyToManyField(settings.AUTH_USER_MODEL, verbose_name=_('Users who voted'), related_name='+', blank=True)

    class Meta:
        abstract = True
        ordering = ("created_at",)

    def recache_votes(self):
        n_votes = self.voters.all().count()
        if n_votes != self.votes:
            self.votes = n_votes
            self.save(update_fields=("votes", ))
