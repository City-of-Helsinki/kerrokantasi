from django.db import models
from django.db.models import FileField
from django.utils.translation import ugettext_lazy as _
from django.core.files.storage import FileSystemStorage
from django.conf import settings

from .base import ORDERING_HELP, BaseModel

protected_storage = FileSystemStorage(location=settings.SENDFILE_ROOT)


class BaseFile(BaseModel):
    uploaded_file = FileField(
        verbose_name=_('file'), max_length=2048, upload_to='files/%Y/%m', storage=protected_storage
    )
    ordering = models.IntegerField(verbose_name=_('ordering'), default=1, db_index=True, help_text=ORDERING_HELP)

    class Meta:
        abstract = True
        ordering = ("ordering")
