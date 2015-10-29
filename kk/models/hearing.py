
from django.conf import settings
from django.contrib.gis.db import models
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from .base import ModifiableModel

class Hearing(ModifiableModel):
    COMMENT_OPTION_DISALLOW = '1'
    COMMENT_OPTION_REGISTERED = '2'
    COMMENT_OPTION_ANONYMOUS = '3'

    COMMENT_OPTION = (
        (COMMENT_OPTION_DISALLOW, 'Disallow'),
        (COMMENT_OPTION_REGISTERED, 'Registered'),
        (COMMENT_OPTION_ANONYMOUS, 'Anonymous')
    )
    close_at = models.DateTimeField(verbose_name=_('Closing time'), default=timezone.now)
    n_comments = models.CharField(verbose_name=_('Number of comments'))
    status = models.BooleanField(verbose_name=_('Whether hearing is open'), default=True)
    heading = models.TextField(verbose_name=_('Heading'), blank=True, default='')
    abstract = models.TextField(verbose_name=_('Abstract'), blank=True, default='')
    heading = models.TextField(verbose_name=_('Content'), blank=True, default='')
    borough = models.CharField(verbose_name=_('Borough to which hearing concerns'), blank=True, default='')
    comment_option = models.CharField(verbose_name=_('Commenting option'), max_length=1, choices=COMMENT_OPTION, default='1')
    servicemap_url = models.CharField(verbose_name=_('Servicemap url'), default='')
    latitude = models.CharField(verbose_name=_('Latitude'), max_length=20, default='')
    longitude = models.CharField(verbose_name=_('Longitude'), max_length=20, default='')


class Label(ModifiableModel):
    hearing = models.ManyToMany(Hearing)
    label = models.CharField(verbose_name=_('Label'), default='')
