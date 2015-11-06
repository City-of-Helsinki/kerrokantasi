from django.db import models
from django.utils.translation import ugettext_lazy as _
from kk.models.comment import BaseComment
from kk.models.images import BaseImage
from .base import BaseModel
from .hearing import Hearing


class Scenario(BaseModel):
    title = models.CharField(verbose_name=_('Title'), max_length=255)
    abstract = models.TextField(verbose_name=_('Abstract'))
    content = models.TextField(verbose_name=_('Content'))
    hearing = models.ForeignKey(Hearing, related_name='scenarios', on_delete=models.PROTECT)

    def __str__(self):
        return "%s: %s" % (self.hearing, self.title)


class ScenarioImage(BaseImage):
    scenario = models.ForeignKey(Scenario, related_name="images")


class ScenarioComment(BaseComment):
    scenario = models.ForeignKey(Scenario, related_name="comments")
