import base64
import struct

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

def generate_id():
    t = time.time() * 1000000
    b = base64.b32encode(struct.pack(">Q", int(t)).lstrip(b'\x00')).strip(b'=').lower()
    return b.decode('utf8')

class ModifiableModel(models.Model):
    id = models.CharField(primary_key=True, max_length=100)
    created_at = models.DateTimeField(verbose_name=_('Time of creation'), default=timezone.now)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('Created by'),
        null=True, blank=True, related_name="%(class)s_created")
    modified_at = models.DateTimeField(verbose_name=_('Time of modification'), default=timezone.now)
    modified_by = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('Modified by'),
        null=True, blank=True, related_name="%(class)s_modified")

    def save(self, *args, **kwargs):
        pk_type = self._meta.pk.get_internal_type()
        if pk_type == 'CharField':
            if not self.pk:
                self.pk = generate_id()
        elif pk_type == 'AutoField':
            pass
        else:
            raise Exception('Unsupported primary key field: %s' % pk_type)
        super().save(*args, **kwargs)

    class Meta:
        abstract = True
