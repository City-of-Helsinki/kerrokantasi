from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.db import models
from django.db.models import FileField
from django.utils.translation import gettext_lazy as _

from democracy.models.base import ORDERING_HELP, BaseModel


class ProtectedFileSystemStorage(FileSystemStorage):
    """
    This subclass exists solely to prevent Django from
    generating migrations for the file storage location.

    E.g. local and production environments might have
    different paths for the protected media, but we don't
    want to generate migrations for that.
    """

    def __init__(self, *args, **kwargs):
        kwargs.update({"location": settings.SENDFILE_ROOT})
        super().__init__(*args, **kwargs)


protected_storage = ProtectedFileSystemStorage()


class BaseFile(BaseModel):
    file = FileField(verbose_name=_("file"), max_length=2048, upload_to="files/%Y/%m", storage=protected_storage)
    ordering = models.IntegerField(verbose_name=_("ordering"), default=1, db_index=True, help_text=ORDERING_HELP)

    class Meta:
        abstract = True
        ordering = "ordering"
