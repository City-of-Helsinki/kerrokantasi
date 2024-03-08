import logging
import re
from autoslug import AutoSlugField
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.urls import get_resolver
from django.utils.translation import gettext_lazy as _
from helsinki_gdpr.models import SerializableMixin
from parler.managers import TranslatableQuerySet
from parler.models import TranslatableModel, TranslatedFields
from reversion import revisions

from democracy.enums import InitialSectionType
from democracy.models.base import (
    ORDERING_HELP,
    BaseModel,
    BaseModelManager,
    Commentable,
    SerializableBaseModelManager,
    StringIdBaseModel,
)
from democracy.models.comment import BaseComment, recache_on_save
from democracy.models.files import BaseFile
from democracy.models.gdpr_data_serialization_mixin import FileFieldUrlSerializerMixin
from democracy.models.hearing import Hearing
from democracy.models.images import BaseImage
from democracy.models.poll import BasePoll, BasePollAnswer, BasePollOption, poll_option_recache_on_save
from democracy.plugins import get_implementation
from democracy.utils.translations import get_translations_dict

CLOSURE_INFO_ORDERING = -10000

INITIAL_SECTION_TYPE_IDS = set(value for key, value in InitialSectionType.__dict__.items() if key[:1] != "_")

LOG = logging.getLogger(__name__)


class SectionTypeQuerySet(models.QuerySet):
    def initial(self):
        return self.filter(identifier__in=INITIAL_SECTION_TYPE_IDS)

    def exclude_initial(self):
        return self.exclude(identifier__in=INITIAL_SECTION_TYPE_IDS)


class SectionType(BaseModel):
    identifier = AutoSlugField(populate_from="name_singular", unique=True)
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


class Section(Commentable, StringIdBaseModel, TranslatableModel, SerializableMixin):
    serialize_fields = (
        {"name": "id"},
        {"name": "ordering"},
        {"name": "title_with_translations"},
        {"name": "abstract_with_translations"},
        {"name": "content_with_translations"},
        {"name": "files"},
        {"name": "images"},
        {"name": "polls"},
    )

    hearing = models.ForeignKey(Hearing, related_name="sections", on_delete=models.PROTECT)
    ordering = models.IntegerField(verbose_name=_("ordering"), default=1, db_index=True, help_text=ORDERING_HELP)
    type = models.ForeignKey(SectionType, related_name="sections", on_delete=models.PROTECT)
    translations = TranslatedFields(
        title=models.CharField(verbose_name=_("title"), max_length=255, blank=True),
        abstract=models.TextField(verbose_name=_("abstract"), blank=True),
        content=models.TextField(verbose_name=_("content"), blank=True),
    )
    plugin_identifier = models.CharField(verbose_name=_("plugin identifier"), blank=True, max_length=255)
    plugin_data = models.TextField(verbose_name=_("plugin data"), blank=True)
    plugin_fullscreen = models.BooleanField(default=False)
    objects = SerializableBaseModelManager.from_queryset(TranslatableQuerySet)()

    class Meta:
        ordering = ["ordering"]
        verbose_name = _("section")
        verbose_name_plural = _("sections")

    @property
    def title_with_translations(self):
        return get_translations_dict(self, "title")

    @property
    def abstract_with_translations(self):
        return get_translations_dict(self, "abstract")

    @property
    def content_with_translations(self):
        return get_translations_dict(self, "content")

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
        url = resolver.reverse_dict.getlist("serve_file")
        if not url:
            LOG.error("serve_file URL pattern not found")
            return 0
        pattern = url[0][1].rstrip("$")

        sectionfile_pks = []
        for translation in self.translations.all():
            for match in re.finditer(pattern, translation.content):
                sectionfile_pks.append(match.groupdict()["pk"])
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


class SectionImage(BaseImage, TranslatableModel, SerializableMixin, FileFieldUrlSerializerMixin):
    field_to_use_as_url_field = "image"

    serialize_fields = (
        {"name": "id"},
        {"name": "title_with_translations"},
        {"name": "caption_with_translations"},
        {"name": "alt_text_with_translations"},
        {"name": "url"},
        {"name": "published"},
        {"name": "created_at"},
        {"name": "modified_at"},
        {"name": "deleted"},
        {"name": "deleted_at"},
    )

    parent_field = "section"
    section = models.ForeignKey(Section, related_name="images", on_delete=models.CASCADE)
    translations = TranslatedFields(
        title=models.CharField(verbose_name=_("title"), max_length=255, blank=True, default=""),
        caption=models.TextField(verbose_name=_("caption"), blank=True, default=""),
        alt_text=models.TextField(verbose_name=_("alt text"), blank=True, default=""),
    )
    objects = SerializableBaseModelManager.from_queryset(TranslatableQuerySet)()

    class Meta:
        verbose_name = _("section image")
        verbose_name_plural = _("section images")
        ordering = ("ordering",)

    @property
    def title_with_translations(self):
        return get_translations_dict(self, "title")

    @property
    def caption_with_translations(self):
        return get_translations_dict(self, "caption")

    @property
    def alt_text_with_translations(self):
        return get_translations_dict(self, "alt_text")


class SectionFile(BaseFile, TranslatableModel, SerializableMixin, FileFieldUrlSerializerMixin):
    field_to_use_as_url_field = "file"

    serialize_fields = (
        {"name": "id"},
        {"name": "title_with_translations"},
        {"name": "caption_with_translations"},
        {"name": "url"},
        {"name": "published"},
        {"name": "created_at"},
        {"name": "modified_at"},
        {"name": "deleted"},
        {"name": "deleted_at"},
    )

    parent_field = "section"
    section = models.ForeignKey(Section, related_name="files", blank=True, null=True, on_delete=models.CASCADE)
    translations = TranslatedFields(
        title=models.CharField(verbose_name=_("title"), max_length=255, blank=True, default=""),
        caption=models.TextField(verbose_name=_("caption"), blank=True, default=""),
    )
    objects = SerializableBaseModelManager.from_queryset(TranslatableQuerySet)()

    class Meta:
        verbose_name = _("section file")
        verbose_name_plural = _("section files")
        ordering = ("ordering",)

    def __str__(self):
        return "%s - %s" % (self.pk, self.file.name)

    @property
    def title_with_translations(self):
        return get_translations_dict(self, "title")

    @property
    def caption_with_translations(self):
        return get_translations_dict(self, "caption")


@revisions.register
@recache_on_save
class SectionComment(Commentable, BaseComment, SerializableMixin):
    serialize_fields = (
        {"name": "id"},
        {"name": "section_id"},
        {"name": "author_name"},
        {"name": "comment_id"},
        {"name": "title"},
        {"name": "content"},
        {"name": "published"},
        {"name": "created_at"},
        {"name": "modified_at"},
        {"name": "deleted"},
        {"name": "deleted_at"},
        {"name": "images"},
        {"name": "poll_answers"},
        {"name": "geojson"},
    )

    parent_field = "section"
    parent_model = Section
    section = models.ForeignKey(Section, related_name="comments", on_delete=models.PROTECT)
    comment = models.ForeignKey("self", related_name="comments", null=True, on_delete=models.SET_NULL)
    title = models.CharField(verbose_name=_("title"), blank=True, max_length=255)
    content = models.TextField(verbose_name=_("content"), blank=True)
    reply_to = models.CharField(verbose_name=_("reply to"), blank=True, max_length=255)
    pinned = models.BooleanField(default=False)
    edited = models.BooleanField(verbose_name=_("is comment edited"), default=False)
    moderated = models.BooleanField(verbose_name=_("is comment edited by admin"), default=False)
    edit_reason = models.TextField(verbose_name=_("edit reason"), blank=True)
    delete_reason = models.TextField(verbose_name=_("delete reason"), blank=True)
    flagged_at = models.DateTimeField(default=None, editable=False, null=True, blank=True)
    flagged_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        related_name="%(class)s_flagged",
        editable=False,
        on_delete=models.SET_NULL,
    )

    objects = SerializableBaseModelManager()

    class Meta:
        verbose_name = _("section comment")
        verbose_name_plural = _("section comments")
        ordering = ("-created_at",)

    def soft_delete(self, user=None):
        for answer in self.poll_answers.all():
            answer.soft_delete(user=user)

        for image in self.images.all():
            image.soft_delete(user=user)

        super().soft_delete(user=user)

    def save(self, *args, **kwargs):
        # we may create a comment by referring to another comment instead of section explicitly
        if not (self.section_id or self.comment_id):
            raise Exception("Section comment must refer to section or another section comment.")
        if not self.section_id:
            self.section_id = self.comment.section_id
        if self.comment_id and self.section_id != self.comment.section_id:
            raise Exception("Comment must belong to the same section as the original comment.")
        super().save(*args, **kwargs)

    def recache_parent_n_comments(self):
        # comments are now commentable but the reference field is not the parent_field
        # therefore we must also recache original comment n_comments field
        if self.comment_id:
            self.comment.recache_n_comments()
        # then update the usual section and hearing n_comments fields
        return super().recache_parent_n_comments()

    def is_commenting_allowed_in_parent(self, request):
        """
        Whether commenting is allowed in the parent of the comment or not.
        """
        try:
            self.parent.check_commenting(request)
        except ValidationError:
            return False
        return True

    def can_edit(self, request):
        """
        Whether the given request (HTTP or DRF) is allowed to edit this Comment.
        """
        if request is None or not request.user.is_authenticated:
            return False

        # Is the user the creator of the comment?
        if request.user == self.created_by:
            return self.is_commenting_allowed_in_parent(request)

        return False

    def can_delete(self, request):
        """
        Whether the given request (HTTP or DRF) is allowed to delete this Comment.
        """
        if request is None or not request.user.is_authenticated:
            return False

        # Is the user the creator of the comment?
        if request.user == self.created_by:
            return self.is_commenting_allowed_in_parent(request)

        return False


class SectionPoll(BasePoll, SerializableMixin):
    serialize_fields = (
        {"name": "id"},
        {"name": "type"},
        {"name": "ordering"},
        {"name": "is_independent_poll"},
        {"name": "text_with_translations"},
        {"name": "options"},
    )
    section = models.ForeignKey(Section, related_name="polls", on_delete=models.PROTECT)
    translations = TranslatedFields(
        text=models.TextField(verbose_name=_("text")),
    )

    objects = SerializableBaseModelManager()

    @property
    def text_with_translations(self):
        return get_translations_dict(self, "text")

    class Meta:
        verbose_name = _("section poll")
        verbose_name_plural = _("section polls")
        ordering = ["ordering"]

    def recache_n_answers(self):
        n_answers = (
            SectionPollAnswer.objects.everything()
            .filter(option__poll_id=self.pk)
            .exclude(option__poll__deleted=True)
            .values("comment_id")
            .distinct()
            .count()
        )
        if n_answers != self.n_answers:
            self.n_answers = n_answers
            self.save(update_fields=("n_answers",))


class SectionPollOption(BasePollOption, SerializableMixin):
    serialize_fields = (
        {"name": "id"},
        {"name": "ordering"},
        {"name": "text_with_translations"},
    )

    @property
    def text_with_translations(self):
        return get_translations_dict(self, "text")

    poll = models.ForeignKey(SectionPoll, related_name="options", on_delete=models.PROTECT)
    translations = TranslatedFields(
        text=models.TextField(verbose_name=_("option text")),
    )

    objects = SerializableBaseModelManager()

    class Meta:
        verbose_name = _("section poll option")
        verbose_name_plural = _("section poll options")
        ordering = ["ordering"]


@poll_option_recache_on_save
class SectionPollAnswer(BasePollAnswer, SerializableMixin):
    serialize_fields = ({"name": "id"}, {"name": "option", "accessor": lambda x: x.text}, {"name": "poll_text"})
    comment = models.ForeignKey(SectionComment, related_name="poll_answers", on_delete=models.CASCADE)
    option = models.ForeignKey(SectionPollOption, related_name="answers", on_delete=models.PROTECT)

    objects = SerializableBaseModelManager()

    @property
    def poll_text(self):
        return get_translations_dict(self.option.poll, "text")

    class Meta:
        verbose_name = _("section poll answer")
        verbose_name_plural = _("section poll answers")


class CommentImage(BaseImage, SerializableMixin, FileFieldUrlSerializerMixin):
    field_to_use_as_url_field = "image"

    serialize_fields = (
        {"name": "id"},
        {"name": "title"},
        {"name": "caption"},
        {"name": "url"},
        {"name": "published"},
        {"name": "created_at"},
        {"name": "modified_at"},
        {"name": "deleted"},
        {"name": "deleted_at"},
    )

    title = models.CharField(verbose_name=_("title"), max_length=255, blank=True, default="")
    caption = models.TextField(verbose_name=_("caption"), blank=True, default="")
    parent_field = "sectioncomment"
    comment = models.ForeignKey(SectionComment, related_name="images", on_delete=models.CASCADE)

    objects = SerializableBaseModelManager()

    class Meta:
        verbose_name = _("comment image")
        verbose_name_plural = _("comment images")
        ordering = ("ordering", "title")
