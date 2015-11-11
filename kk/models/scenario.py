from django.db import models
from django.db.models.signals import post_save
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

import reversion
from kk.models.comment import BaseComment
from kk.models.images import BaseImage

from .base import BaseModel, WithCommentsMixin
from .hearing import Hearing


class Scenario(WithCommentsMixin, BaseModel):
    title = models.CharField(verbose_name=_('Title'), max_length=255)
    abstract = models.TextField(verbose_name=_('Abstract'))
    content = models.TextField(verbose_name=_('Content'))
    hearing = models.ForeignKey(Hearing, related_name='scenarios', on_delete=models.PROTECT)

    def __str__(self):
        return "%s: %s" % (self.hearing, self.title)


class ScenarioImage(BaseImage):
    scenario = models.ForeignKey(Scenario, related_name="images")


@reversion.register
class ScenarioComment(BaseComment):
    parent_field = "scenario"
    parent_model = Scenario
    scenario = models.ForeignKey(Scenario, related_name="comments")


def scenario_recache(sender, instance, using, **kwargs):
    # recache number of comments
    instance.scenario.recache_n_comments()
    # also, recache number of votes
    instance.recache_n_votes()

post_save.connect(scenario_recache, sender=ScenarioComment)
