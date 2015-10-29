
from django.conf import settings
from django.contrib.gis.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

class ModifiableModel(models.Model):
    created_at = models.DateTimeField(verbose_name=_('Time of creation'), default=timezone.now)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('Created by'),
        null=True, blank=True, related_name="%(class)s_created")
    modified_at = models.DateTimeField(verbose_name=_('Time of modification'), default=timezone.now)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('Modified by'),
        null=True, blank=True, related_name="%(class)s_modified")
    
    class Meta:
        abstract = True
