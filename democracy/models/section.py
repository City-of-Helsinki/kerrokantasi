import logging
import re
from autoslug import AutoSlugField
from django.conf import settings
from django.db import models
from django.urls import get_resolver
from django.utils.translation import ugettext_lazy as _
from parler.managers import TranslatableQuerySet
from parler.models import TranslatableModel, TranslatedFields
from reversion import revisions

from democracy.enums import InitialSectionType
from democracy.models.base import ORDERING_HELP, BaseModel, BaseModelManager, Commentable, StringIdBaseModel
from democracy.models.comment import BaseComment, recache_on_save
from democracy.models.files import BaseFile
from democracy.models.hearing import Hearing
from democracy.models.images import BaseImage
from democracy.models.poll import BasePoll, BasePollAnswer, BasePollOption, poll_option_recache_on_save
from democracy.plugins import get_implementation

CLOSURE_INFO_ORDERING = -10000

INITIAL_SECTION_TYPE_IDS = set(value for key, value in InitialSectionType.__dict__.items() if key[:1] != '_')

LOG = logging.getLogger(__name__)


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


class Section(Commentable, StringIdBaseModel, TranslatableModel):
    hearing = models.ForeignKey(Hearing, related_name='sections', on_delete=models.PROTECT)
    ordering = models.IntegerField(verbose_name=_('ordering'), default=1, db_index=True, help_text=ORDERING_HELP)
    type = models.ForeignKey(SectionType, related_name='sections', on_delete=models.PROTECT)
    translations = TranslatedFields(
        title=models.CharField(verbose_name=_('title'), max_length=255, blank=True),
        abstract=models.TextField(verbose_name=_('abstract'), blank=True),
        content=models.TextField(verbose_name=_('content'), blank=True),
    )
    plugin_identifier = models.CharField(verbose_name=_('plugin identifier'), blank=True, max_length=255)
    plugin_data = models.TextField(verbose_name=_('plugin data'), blank=True)
    plugin_fullscreen = models.BooleanField(default=False)
    objects = BaseModelManager.from_queryset(TranslatableQuerySet)()

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
        obj = super(Section, self).save(*args, **kwargs)
        self.claim_orphan_files()
        return obj

    def claim_orphan_files(self):
        """
        While creating the Section files might have been uploaded that should be
        linked to the Section. Try to find such SectionFile objects and
        link them.

        CKEditor creates plain old <a> elements for uploaded files. We have to
        parse the section content to figure out if there are new files.
        """
        # get regex pattern of protected sectionfile endpoint
        resolver = get_resolver(None)
        url = resolver.reverse_dict.getlist('serve_file')
        if not url:
            LOG.error('serve_file URL pattern not found')
            return 0
        pattern = url[0][1].rstrip('$')

        sectionfile_pks = []
        for translation in self.translations.all():
            for match in re.finditer(pattern, translation.content):
                sectionfile_pks.append(match.groupdict()['pk'])
        return SectionFile.objects.filter(section__isnull=True, pk__in=sectionfile_pks).update(section_id=self.pk)

    def check_commenting(self, request):
        super().check_commenting(request)
        self.hearing.check_commenting(request)

    def check_voting(self, request):
        super().check_voting(request)
        self.hearing.check_voting(request)

    @property
    def plugin_implementation(self):
        return get_implementation(self.plugin_identifier)


class SectionImage(BaseImage, TranslatableModel):
    parent_field = "section"
    section = models.ForeignKey(Section, related_name="images", on_delete=models.CASCADE)
    translations = TranslatedFields(
        title=models.CharField(verbose_name=_('title'), max_length=255, blank=True, default=''),
        caption=models.TextField(verbose_name=_('caption'), blank=True, default=''),
        alt_text=models.TextField(verbose_name=_('alt text'), blank=True, default=''),
    )
    objects = BaseModelManager.from_queryset(TranslatableQuerySet)()

    class Meta:
        verbose_name = _('section image')
        verbose_name_plural = _('section images')
        ordering = ('ordering',)


class SectionFile(BaseFile, TranslatableModel):
    parent_field = "section"
    section = models.ForeignKey(Section, related_name="files", blank=True, null=True, on_delete=models.CASCADE)
    translations = TranslatedFields(
        title=models.CharField(verbose_name=_('title'), max_length=255, blank=True, default=''),
        caption=models.TextField(verbose_name=_('caption'), blank=True, default=''),
    )
    objects = BaseModelManager.from_queryset(TranslatableQuerySet)()

    class Meta:
        verbose_name = _('section file')
        verbose_name_plural = _('section files')
        ordering = ('ordering',)

    def __str__(self):
        return '%s - %s' % (self.pk, self.file.name)


@revisions.register
@recache_on_save
class SectionComment(Commentable, BaseComment):
    parent_field = "section"
    parent_model = Section
    section = models.ForeignKey(Section, related_name="comments", on_delete=models.PROTECT)
    comment = models.ForeignKey('self', related_name="comments", null=True, on_delete=models.SET_NULL)
    title = models.CharField(verbose_name=_('title'), blank=True, max_length=255)
    content = models.TextField(verbose_name=_('content'), blank=True)
    reply_to = models.CharField(verbose_name=_('reply to'), blank=True, max_length=255)
    pinned = models.BooleanField(default=False)
    delete_reason = models.TextField(verbose_name=_('delete reason'), blank=True)
    flagged_at = models.DateTimeField(default=None, editable=False, null=True, blank=True)
    flagged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True, blank=True, related_name="%(class)s_flagged",
        editable=False, on_delete=models.SET_NULL
    )

    class Meta:
        verbose_name = _('section comment')
        verbose_name_plural = _('section comments')
        ordering = ('-created_at',)

    def soft_delete(self, using=None, user=None):
        for answer in self.poll_answers.all():
            answer.soft_delete(user=user)
        super().soft_delete(using=using, user=user)

    def save(self, *args, **kwargs):
        # we may create a comment by referring to another comment instead of section explicitly
        if not (self.section or self.comment):
            raise Exception('Section comment must refer to section or another section comment.')
        if not self.section:
            self.section = self.comment.section
        if self.comment and self.section != self.comment.section:
            raise Exception('Comment must belong to the same section as the original comment.')
        super().save(*args, **kwargs)

    def recache_parent_n_comments(self):
        # comments are now commentable but the reference field is not the parent_field
        # therefore we must also recache original comment n_comments field
        if self.comment_id:
            self.comment.recache_n_comments()
        # then update the usual section and hearing n_comments fields
        return super().recache_parent_n_comments()


class SectionPoll(BasePoll):
    section = models.ForeignKey(Section, related_name='polls', on_delete=models.PROTECT)
    translations = TranslatedFields(
        text=models.TextField(verbose_name=_('text')),
    )

    class Meta:
        verbose_name = _('section poll')
        verbose_name_plural = _('section polls')
        ordering = ['ordering']

    def recache_n_answers(self):
        n_answers = (
            SectionPollAnswer.objects
            .everything()
            .filter(option__poll_id=self.pk)
            .exclude(option__poll__deleted=True)
            .values('comment_id')
            .distinct()
            .count()
        )
        if n_answers != self.n_answers:
            self.n_answers = n_answers
            self.save(update_fields=('n_answers',))


class SectionPollOption(BasePollOption):
    poll = models.ForeignKey(SectionPoll, related_name='options', on_delete=models.PROTECT)
    translations = TranslatedFields(
        text=models.TextField(verbose_name=_('option text')),
    )

    class Meta:
        verbose_name = _('section poll option')
        verbose_name_plural = _('section poll options')
        ordering = ['ordering']


@poll_option_recache_on_save
class SectionPollAnswer(BasePollAnswer):
    comment = models.ForeignKey(SectionComment, related_name='poll_answers', on_delete=models.CASCADE)
    option = models.ForeignKey(SectionPollOption, related_name='answers', on_delete=models.PROTECT)

    class Meta:
        verbose_name = _('section poll answer')
        verbose_name_plural = _('section poll answers')


class CommentImage(BaseImage):
    title = models.CharField(verbose_name=_('title'), max_length=255, blank=True, default='')
    caption = models.TextField(verbose_name=_('caption'), blank=True, default='')
    parent_field = "sectioncomment"
    comment = models.ForeignKey(SectionComment, related_name="images", on_delete=models.CASCADE)

    class Meta:
        verbose_name = _('comment image')
        verbose_name_plural = _('comment images')
        ordering = ("ordering", "title")
