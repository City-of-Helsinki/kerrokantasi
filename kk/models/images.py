from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _
from django.core.files.storage import FileSystemStorage

from .base import ModifiableModel
from .hearing import Hearing

def get_images_dir():
    return '%s/%s/' % (settings.BASE_DIR, settings.IMAGES_DIR)

file_storage = FileSystemStorage(location=get_images_dir())

class CommonImage(ModifiableModel):
    IMAGE_TYPE_ORIGINAL = '1'
    IMAGE_TYPE_SMALL = '2'
    IMAGE_TYPE_THUMBNAIL = '3'

    IMAGE_TYPE = (
        (IMAGE_TYPE_ORIGINAL, 'Original'),
        (IMAGE_TYPE_SMALL, 'Small'),
        (IMAGE_TYPE_THUMBNAIL, 'Thumbnail')
    )
    type = models.CharField(verbose_name=_('The type of the image'), max_length=1, choices=IMAGE_TYPE, default='1')
    title = models.CharField(verbose_name=_('The title'), max_length=255, blank=True, default='')
    caption = models.TextField(verbose_name=_('Caption'), blank=True, default='')
    height = models.CharField(verbose_name=_('Height'), max_length=10, blank=True, default='')
    width = models.CharField(verbose_name=_('Width'), max_length=10, blank=True, default='')
    image = models.ImageField(verbose_name=_('Image'), storage=file_storage)

    class Meta:
        abstract = True

class HearingImage(CommonImage):
    hearing = models.ForeignKey(Hearing, related_name='images', on_delete=models.SET_NULL, null=True)
