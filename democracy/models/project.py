from django.db import models
from django.utils.translation import gettext_lazy as _
from parler.managers import TranslatableQuerySet
from parler.models import TranslatableModel, TranslatedFields

from democracy.models.base import ORDERING_HELP, BaseModelManager, StringIdBaseModel


class Project(StringIdBaseModel, TranslatableModel):
    """
    Multi-phase project containing related hearings.

    Projects group related hearings into a coherent timeline with multiple phases.
    Each hearing is associated with exactly one active phase at a time.
    """

    identifier = models.CharField(
        max_length=50,
        verbose_name=_("identifier"),
        db_index=True,
        blank=True,
        null=True,
        help_text=_("External identifier for system integration"),
    )
    translations = TranslatedFields(
        title=models.CharField(
            verbose_name=_("title"),
            max_length=255,
            blank=True,
            help_text=_("Project title for grouping related hearings"),
        ),
    )
    objects = BaseModelManager.from_queryset(TranslatableQuerySet)()

    def __str__(self):
        return self.title or self.pk


class ProjectPhase(StringIdBaseModel, TranslatableModel):
    """
    Individual phase within a multi-phase project.

    Each project consists of multiple phases that represent different stages
    or milestones. Hearings are associated with specific phases, and each
    hearing must have exactly one active phase.
    """

    translations = TranslatedFields(
        title=models.CharField(
            verbose_name=_("title"),
            max_length=255,
            blank=True,
            help_text=_("Phase title within the project timeline"),
        ),
        description=models.CharField(
            verbose_name=_("description"),
            max_length=2048,
            blank=True,
            help_text=_("Detailed description of this project phase"),
        ),
        schedule=models.CharField(
            verbose_name=_("schedule"),
            max_length=2048,
            blank=True,
            help_text=_("Timeline and schedule information for this phase"),
        ),
    )
    project = models.ForeignKey(
        Project,
        related_name="phases",
        on_delete=models.CASCADE,
        help_text=_("Project this phase belongs to"),
    )
    ordering = models.IntegerField(
        verbose_name=_("ordering"), default=1, db_index=True, help_text=ORDERING_HELP
    )
    objects = BaseModelManager.from_queryset(TranslatableQuerySet)()

    class Meta:
        ordering = ("ordering",)

    def __str__(self):
        project = self.project.title or self.project.pk
        title = self.title or self.pk
        return "%s: %s" % (project, title)
