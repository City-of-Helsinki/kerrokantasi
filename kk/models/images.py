from django.db import models
from django.db.models import ImageField
from django.utils.translation import ugettext_lazy as _
from .base import BaseModel


class BaseImage(BaseModel):
    title = models.CharField(verbose_name=_('The title'), max_length=255, blank=True, default='')
    caption = models.TextField(verbose_name=_('Caption'), blank=True, default='')
    height = models.IntegerField(verbose_name=_('Height'), default=0, editable=False)
    width = models.IntegerField(verbose_name=_('Width'), default=0, editable=False)
    image = ImageField(verbose_name=_('Image'), upload_to='images/%Y/%m', width_field='width', height_field='height')
    ordering = models.IntegerField(verbose_name=_('Ordering'), default=0, db_index=True)

    class Meta:
        abstract = True
        ordering = ("ordering", "title")
