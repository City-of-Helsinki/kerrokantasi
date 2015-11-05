from django.db import models
from django.utils.translation import ugettext_lazy as _

from .base import ModifiableModel
from .images import WithImageMixin
from .hearing import Hearing


class Introduction(WithImageMixin, ModifiableModel):
    abstract = models.TextField(verbose_name=_('Abstract'))
    content = models.TextField(verbose_name=_('Content'))
    hearing = models.ForeignKey(
        Hearing, related_name='introductions', on_delete=models.SET_NULL, null=True)
