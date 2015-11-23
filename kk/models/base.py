from functools import lru_cache

from django.conf import settings
from django.db import models
from django.db.models import ManyToOneRel
from django.utils import timezone
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _
from enumfields.fields import EnumIntegerField

from kk.enums import Commenting


def generate_id():
    return get_random_string(32)


class BaseModelManager(models.Manager):

    def get_queryset(self):
        return super().get_queryset().exclude(deleted=True)

    def deleted(self):
        return super().get_queryset().filter(deleted=True)


class BaseModel(models.Model):
    created_at = models.DateTimeField(verbose_name=_('Time of creation'), default=timezone.now, editable=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('Created by'),
        null=True, blank=True, related_name="%(class)s_created",
        editable=False
    )
    modified_at = models.DateTimeField(verbose_name=_('Time of modification'), default=timezone.now, editable=False)
    modified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, verbose_name=_('Modified by'),
        null=True, blank=True, related_name="%(class)s_modified",
        editable=False
    )
    deleted = models.BooleanField(
        verbose_name=_('Deleted flag'), default=False, db_index=True,
        editable=False
    )
    objects = BaseModelManager()

    def save(self, *args, **kwargs):
        pk_type = self._meta.pk.get_internal_type()
        if pk_type == 'CharField':
            if not self.pk:
                self.pk = generate_id()
        elif pk_type == 'AutoField':
            pass
        else:
            raise Exception('Unsupported primary key field: %s' % pk_type)
        self.modified_at = timezone.now()
        super().save(*args, **kwargs)

    def soft_delete(self, using=None):
        self.deleted = True
        self.save(update_fields=("deleted",), using=using, force_update=True)

    def delete(self, using=None):
        raise NotImplementedError("This model does not support hard deletion")

    @classmethod
    @lru_cache()
    def find_subclass(cls, parent_model):
        """
        Find the subclass that's used with the given `parent_model`.

        This is only useful for models that are related to another model, such
        as Comments or Images.

        :param parent_model: A model (class or instance)
        :return: The model subclass, or None
        :rtype: class|None
        """
        for field in parent_model._meta.get_fields():
            if isinstance(field, ManyToOneRel):
                if issubclass(field.related_model, cls):
                    return field.related_model

    class Meta:
        abstract = True


class StringIdBaseModel(BaseModel):
    id = models.CharField(
        primary_key=True,
        max_length=32,
        blank=True,
        help_text=_('You may leave this empty to automatically generate an ID')
    )

    class Meta:
        abstract = True


class Commentable(models.Model):
    """
    Mixin for models which can be commented.
    """
    n_comments = models.IntegerField(verbose_name=_('Number of comments'), blank=True, default=0, editable=False)
    commenting = EnumIntegerField(Commenting, default=Commenting.NONE)

    def recache_n_comments(self):
        new_n_comments = self.comments.count()
        if new_n_comments != self.n_comments:
            self.n_comments = new_n_comments
            self.save(update_fields=("n_comments",))

    def may_comment(self, request):
        if self.commenting == Commenting.NONE:
            return False
        elif self.commenting == Commenting.OPEN:
            return True
        elif self.commenting == Commenting.REGISTERED:
            return request.user.is_authenticated()
        else:  # pragma: no cover
            raise NotImplementedError("Not implemented")

    class Meta:
        abstract = True
