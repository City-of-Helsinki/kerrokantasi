from django.db import models
from django.template.defaultfilters import truncatewords
from django.utils.translation import ugettext_lazy as _
from .base import BaseModel
from .images import BaseImage
from .hearing import Hearing


class Introduction(BaseModel):
    abstract = models.TextField(verbose_name=_('Abstract'))
    content = models.TextField(verbose_name=_('Content'))
    hearing = models.ForeignKey(Hearing, related_name='introductions', on_delete=models.PROTECT)

    def __str__(self):
        return "%s: %s" % (self.hearing, truncatewords(self.abstract, 30))


class IntroductionImage(BaseImage):
    hearing = models.ForeignKey(Introduction, related_name="images")
