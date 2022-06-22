from django.db import models
from django.db.models import ImageField
from django.utils.translation import ugettext_lazy as _

from democracy.models.base import ORDERING_HELP, BaseModel


class BaseImage(BaseModel):
    height = models.IntegerField(verbose_name=_('height'), default=0, editable=False)
    width = models.IntegerField(verbose_name=_('width'), default=0, editable=False)
    image = ImageField(verbose_name=_('image'), upload_to='images/%Y/%m', width_field='width', height_field='height')
    ordering = models.IntegerField(verbose_name=_('ordering'), default=1, db_index=True, help_text=ORDERING_HELP)

    class Meta:
        abstract = True
        ordering = ("ordering")
