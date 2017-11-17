from django.db import models
from django.utils.translation import ugettext_lazy as _
from parler.models import TranslatedFields, TranslatableModel
from parler.managers import TranslatableQuerySet

from .base import BaseModel, BaseModelManager


class Label(BaseModel, TranslatableModel):
    translations = TranslatedFields(
        label=models.CharField(verbose_name=_('label'), default='', max_length=200),
    )
    objects = BaseModelManager.from_queryset(TranslatableQuerySet)()

    class Meta:
        verbose_name = _('label')
        verbose_name_plural = _('labels')

    def __str__(self):
        return self.label
