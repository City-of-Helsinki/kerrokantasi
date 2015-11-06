from django.db import models
from django.utils.translation import ugettext_lazy as _

from .base import ModifiableModel
from .hearing import Hearing
from .images import WithImageMixin


class Scenario(WithImageMixin, ModifiableModel):
    title = models.CharField(verbose_name=_('Title'), max_length=255)
    abstract = models.TextField(verbose_name=_('Abstract'))
    content = models.TextField(verbose_name=_('Content'))
    hearing = models.ForeignKey(
        Hearing, related_name='scenarios', on_delete=models.SET_NULL, null=True)
