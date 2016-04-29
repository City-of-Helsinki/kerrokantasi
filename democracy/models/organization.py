from .base import StringIdBaseModel
from django.db import models
from django.conf import settings
from django.utils.translation import ugettext_lazy as _


class Organization(StringIdBaseModel):
    name = models.CharField(verbose_name=_('name'), max_length=255, unique=True)
    admin_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name='admin_organizations'
    )

    class Meta:
        verbose_name = _('organization')
        verbose_name_plural = _('organizations')

    def __str__(self):
        return self.name
