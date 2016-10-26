from django.db import models
from django.utils.translation import ugettext_lazy as _
from reversion import revisions
from autoslug import AutoSlugField

from democracy.models.comment import BaseComment, recache_on_save
from democracy.models.images import BaseImage
from democracy.plugins import get_implementation

from democracy.enums import InitialSectionType
from .base import ORDERING_HELP, Commentable, StringIdBaseModel, BaseModel, BaseModelManager
from .hearing import Hearing

CLOSURE_INFO_ORDERING = -10000

INITIAL_SECTION_TYPE_IDS = set(value for key, value in InitialSectionType.__dict__.items() if key[:1] != '_')


class SectionTypeQuerySet(models.QuerySet):
    def initial(self):
        return self.filter(identifier__in=INITIAL_SECTION_TYPE_IDS)

    def exclude_initial(self):
        return self.exclude(identifier__in=INITIAL_SECTION_TYPE_IDS)


class SectionType(BaseModel):
    identifier = AutoSlugField(populate_from='name_singular', unique=True)
    name_singular = models.CharField(max_length=64)
    name_plural = models.CharField(max_length=64)
    objects = BaseModelManager.from_queryset(SectionTypeQuerySet)()

    def __str__(self):
        return self.name_singular

    def save(self, *args, **kwargs):
        # prevent initial type editing
        if self.identifier in INITIAL_SECTION_TYPE_IDS:
            raise Exception("Initial section types cannot be edited.")
        return super().save(*args, **kwargs)


class Section(Commentable, StringIdBaseModel):
    hearing = models.ForeignKey(Hearing, related_name='sections', on_delete=models.PROTECT)
    ordering = models.IntegerField(verbose_name=_('ordering'), default=1, db_index=True, help_text=ORDERING_HELP)
    type = models.ForeignKey(SectionType, related_name='sections', on_delete=models.PROTECT)
    title = models.CharField(verbose_name=_('title'), max_length=255, blank=True)
    abstract = models.TextField(verbose_name=_('abstract'), blank=True)
    content = models.TextField(verbose_name=_('content'), blank=True)
    plugin_identifier = models.CharField(verbose_name=_('plugin identifier'), blank=True, max_length=255)
    plugin_data = models.TextField(verbose_name=_('plugin data'), blank=True)

    class Meta:
        ordering = ["ordering"]
        verbose_name = _('section')
        verbose_name_plural = _('sections')

    def __str__(self):
        return "%s: %s" % (self.hearing, self.title)

    def save(self, *args, **kwargs):
        if self.hearing_id:
            # Closure info should be the first
            if self.type == SectionType.objects.get(identifier=InitialSectionType.CLOSURE_INFO):
                self.ordering = CLOSURE_INFO_ORDERING
            elif (not self.pk and self.ordering == 1) or self.ordering == CLOSURE_INFO_ORDERING:
                # This is a new section or changing type from closure info,
                # automatically derive next ordering, if possible
                self.ordering = max(self.hearing.sections.values_list("ordering", flat=True) or [0]) + 1
        return super(Section, self).save(*args, **kwargs)

    def check_commenting(self, request):
        super().check_commenting(request)
        self.hearing.check_commenting(request)

    def check_voting(self, request):
        super().check_voting(request)
        self.hearing.check_voting(request)

    @property
    def plugin_implementation(self):
        return get_implementation(self.plugin_identifier)


class SectionImage(BaseImage):
    parent_field = "section"
    section = models.ForeignKey(Section, related_name="images")

    class Meta:
        verbose_name = _('section image')
        verbose_name_plural = _('section images')


@revisions.register
@recache_on_save
class SectionComment(BaseComment):
    parent_field = "section"
    parent_model = Section
    section = models.ForeignKey(Section, related_name="comments")

    class Meta:
        verbose_name = _('section comment')
        verbose_name_plural = _('section comments')
        ordering = ('-created_at',)


class CommentImage(BaseImage):
    parent_field = "sectioncomment"
    comment = models.ForeignKey(SectionComment, related_name="images")

    class Meta:
        verbose_name = _('comment image')
        verbose_name_plural = _('comment images')
