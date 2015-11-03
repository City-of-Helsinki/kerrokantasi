from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.core.files.storage import FileSystemStorage
from easy_thumbnails.fields import ThumbnailerImageField

from .base import ModifiableModel
from .hearing import Hearing

def get_images_dir():
    return settings.IMAGES_DIR

file_storage = FileSystemStorage(location=get_images_dir())

class CommonImage(ModifiableModel):
    title = models.CharField(verbose_name=_('The title'), max_length=255, blank=True, default='')
    caption = models.TextField(verbose_name=_('Caption'), blank=True, default='')
    height = models.IntegerField(verbose_name=_('Height'), default=0)
    width = models.IntegerField(verbose_name=_('Width'), default=0)
    image = ThumbnailerImageField(verbose_name=_('Image'), storage=file_storage, resize_source=dict(size=(100, 100), sharpen=True))    

    class Meta:
        abstract = True

class HearingImage(CommonImage):
    hearing = models.ForeignKey(Hearing, related_name='images', on_delete=models.SET_NULL, null=True)
