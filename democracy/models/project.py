import logging
from django.db import models
from django.utils.translation import ugettext_lazy as _
from parler.managers import TranslatableQuerySet
from parler.models import TranslatableModel, TranslatedFields

from democracy.models.base import ORDERING_HELP, BaseModelManager, StringIdBaseModel

LOG = logging.getLogger(__name__)


class Project(StringIdBaseModel, TranslatableModel):
    identifier = models.CharField(max_length=50, verbose_name=_('identifier'), db_index=True, blank=True, null=True)
    translations = TranslatedFields(
        title=models.CharField(verbose_name=_('title'), max_length=255, blank=True),
    )
    objects = BaseModelManager.from_queryset(TranslatableQuerySet)()

    def __str__(self):
        return (self.title or self.pk)


class ProjectPhase(StringIdBaseModel, TranslatableModel):
    translations = TranslatedFields(
        title=models.CharField(verbose_name=_('title'), max_length=255, blank=True),
        description=models.CharField(verbose_name=_('description'), max_length=2048, blank=True),
        schedule=models.CharField(verbose_name=_('schedule'), max_length=2048, blank=True),
    )
    project = models.ForeignKey(Project, related_name='phases', on_delete=models.CASCADE)
    ordering = models.IntegerField(verbose_name=_('ordering'), default=1, db_index=True, help_text=ORDERING_HELP)
    objects = BaseModelManager.from_queryset(TranslatableQuerySet)()

    class Meta:
        ordering = ('ordering',)

    def __str__(self):
        project = self.project.title or self.project.pk
        title = self.title or self.pk
        return '%s: %s' % (project, title)
