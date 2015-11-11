from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from .base import BaseModel


class BaseComment(BaseModel):
    parent_field = None  # Required for factories and API
    parent_model = None  # Required for factories and API
    content = models.TextField(verbose_name=_('Content'))
    n_votes = models.IntegerField(verbose_name=_('Votes given to this comment'), default=0, editable=False)
    followers = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name=_('Users who follow'),
        related_name="followed_%(app_label)s_%(class)s",
        blank=True
    )
    voters = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name=_('Users who voted'),
        related_name="voted_%(app_label)s_%(class)s",
        blank=True
    )

    class Meta:
        abstract = True
        ordering = ("created_at",)

    def recache_n_votes(self):
        n_votes = self.voters.all().count()
        if n_votes != self.n_votes:
            self.n_votes = n_votes
            self.save(update_fields=("n_votes", ))
