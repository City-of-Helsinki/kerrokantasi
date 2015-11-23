from django.conf import settings
from django.db import models
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _

from .base import BaseModel


class BaseComment(BaseModel):
    parent_field = None  # Required for factories and API
    parent_model = None  # Required for factories and API
    title = models.CharField(blank=True, max_length=80)
    content = models.TextField(verbose_name=_('Content'))
    author_name = models.CharField(max_length=40, blank=True, null=True)
    n_votes = models.IntegerField(verbose_name=_('Votes given to this comment'), default=0, editable=False)
    voters = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        verbose_name=_('Users who voted'),
        related_name="voted_%(app_label)s_%(class)s",
        blank=True
    )

    class Meta:
        abstract = True
        ordering = ("created_at",)

    @property
    def parent(self):
        """
        :rtype: Commentable|None
        """
        return getattr(self, self.parent_field, None)

    @property
    def parent_id(self):
        """
        :rtype: int|str|None
        """
        return getattr(self, "%s_id" % self.parent_field, None)

    def save(self, *args, **kwargs):
        self.author_name = (str(self.created_by) if self.created_by_id else None)
        return super(BaseComment, self).save(*args, **kwargs)

    def recache_n_votes(self):
        n_votes = self.voters.all().count()
        if n_votes != self.n_votes:
            self.n_votes = n_votes
            self.save(update_fields=("n_votes", ))

    def recache_parent_n_comments(self):
        if self.parent_id:  # pragma: no branch
            self.parent.recache_n_comments()


def comment_recache(sender, instance, using, created, **kwargs):
    """
    :type instance: BaseComment
    """
    if created or instance.deleted:
        instance.recache_parent_n_comments()
    else:
        instance.recache_n_votes()


def recache_on_save(klass):
    assert issubclass(klass, BaseComment)
    post_save.connect(comment_recache, sender=klass)
    return klass
