from django.db import models
from django.utils.translation import gettext_lazy as _
from parler.managers import TranslatableQuerySet
from parler.models import TranslatableModel, TranslatedFields

from democracy.models.base import BaseModel, BaseModelManager


class Label(BaseModel, TranslatableModel):
    translations = TranslatedFields(
        label=models.CharField(verbose_name=_("label"), default="", max_length=200),
    )
    objects = BaseModelManager.from_queryset(TranslatableQuerySet)()

    class Meta:
        verbose_name = _("label")
        verbose_name_plural = _("labels")

    def __str__(self):
        return self.label
