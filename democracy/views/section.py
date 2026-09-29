from functools import lru_cache
from html.parser import HTMLParser
from urllib.parse import unquote, urlsplit

import django_filters
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.db import transaction
from django.db.models import Max, Prefetch, Q
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.views.generic import View
from django.views.generic.detail import SingleObjectMixin
from django_sendfile import sendfile
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_field,
    extend_schema_view,
)
from easy_thumbnails.files import get_thumbnailer
from rest_framework import permissions, serializers, viewsets
from rest_framework.exceptions import ParseError, PermissionDenied, ValidationError

from audit_log.views import AuditLogApiView
from democracy.enums import Commenting, CommentingMapTools, InitialSectionType
from democracy.models import (
    Hearing,
    Section,
    SectionFile,
    SectionImage,
    SectionPoll,
    SectionPollOption,
    SectionType,
)
from democracy.pagination import DefaultLimitPagination
from democracy.utils.drf_enum_field import EnumField
from democracy.views.base import (
    AdminsSeeUnpublishedMixin,
    BaseFileSerializer,
    BaseImageSerializer,
)
from democracy.views.utils import (
    Base64FileField,
    Base64ImageField,
    TranslatableSerializer,
    compare_serialized,
    filter_by_hearing_visible,
    validate_image_size,
)

# Section-specific OpenAPI parameters
SECTION_IMAGE_PARAMS = [
    OpenApiParameter(
        "section_type",
        OpenApiTypes.STR,
        description="Filter by section type identifier",
    ),
    OpenApiParameter(
        "dim",
        OpenApiTypes.STR,
        description="Image dimensions for thumbnail (e.g., '640x480')",
    ),
]

DIM_PARAM = [
    OpenApiParameter(
        "dim",
        OpenApiTypes.STR,
        description="Image dimensions for thumbnail (e.g., '640x480')",
        location=OpenApiParameter.QUERY,
    ),
]


class InlineImageSourceParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sources = set()

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "img" and (source := dict(attrs).get("src")):
            self.sources.add(source)


def get_inline_image_urls(content):
    urls = set()
    for html in content.values():
        parser = InlineImageSourceParser()
        parser.feed(html or "")
        parser.close()
        urls.update(parser.sources)
    return urls


def get_inline_image_name(image_url):
    media_url_path = urlsplit(settings.MEDIA_URL).path
    if not media_url_path:
        return None

    media_url_path = media_url_path.rstrip("/") + "/"
    path = urlsplit(image_url).path
    if path.startswith(media_url_path):
        return unquote(path[len(media_url_path) :])
    return None


class ThumbnailImageSerializer(BaseImageSerializer):
    """
    Image serializer supporting thumbnails via GET parameter

    ?dim=640x480
    """

    width = serializers.SerializerMethodField()
    height = serializers.SerializerMethodField()

    def get_width(self, obj):
        request = self._get_context_request()
        if request and "dim" in request.GET:
            try:
                width, _height = self._parse_dimension_string(request.GET["dim"])
                return width
            except ValueError as verr:
                raise ParseError(detail=str(verr), code="invalid-dim-parameter")
        return obj.width

    def get_height(self, obj):
        request = self._get_context_request()
        if request and "dim" in request.GET:
            try:
                _width, height = self._parse_dimension_string(request.GET["dim"])
                return height
            except ValueError as verr:
                raise ParseError(detail=str(verr), code="invalid-dim-parameter")
        return obj.height

    def _get_image(self, obj):
        request = self._get_context_request()
        if request and "dim" in request.GET:
            try:
                width, height = self._parse_dimension_string(request.GET["dim"])
            except ValueError as verr:
                raise ParseError(detail=str(verr), code="invalid-dim-parameter")
            return get_thumbnailer(obj.image).get_thumbnail(
                {
                    "size": (width, height),
                    "crop": "smart",
                }
            )
        else:
            return obj.image

    @staticmethod
    @lru_cache()
    def _parse_dimension_string(dim):
        """
        Parse a dimension string ("WxH") into (width, height).
        :param dim: Dimension string
        :type dim: str
        :return: Dimension tuple
        :rtype: tuple[int, int]
        """
        a = dim.split("x")
        if len(a) != 2:
            raise ValueError('"dim" must be <width>x<height>')
        width, height = a
        try:
            width = int(width)
            height = int(height)
        except ValueError:
            width = height = 0
        if not (width > 0 and height > 0):
            raise ValueError("width and height must be positive integers")
        return width, height


class SectionImageSerializer(ThumbnailImageSerializer, TranslatableSerializer):
    class Meta:
        model = SectionImage
        fields = [
            "id",
            "title",
            "url",
            "width",
            "height",
            "caption",
            "alt_text",
        ]


class SectionImageCreateUpdateSerializer(BaseImageSerializer, TranslatableSerializer):
    image = Base64ImageField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # image content isn't mandatory on updates
        if self.instance:
            self.fields["image"].required = False

    class Meta:
        model = SectionImage
        fields = [
            "title",
            "url",
            "width",
            "height",
            "caption",
            "alt_text",
            "image",
            "ordering",
        ]


class SectionFileSerializer(BaseFileSerializer, TranslatableSerializer):
    filetype = "sectionfile"

    class Meta:
        model = SectionFile
        fields = ["id", "title", "url", "caption"]


class SectionPollOptionSerializer(serializers.ModelSerializer, TranslatableSerializer):
    class Meta:
        model = SectionPollOption
        fields = ["id", "text", "n_answers"]


class SectionPollSerializer(serializers.ModelSerializer, TranslatableSerializer):
    options = serializers.ListField(child=serializers.DictField(), write_only=True)

    class Meta:
        model = SectionPoll
        fields = ["id", "type", "text", "options", "n_answers", "is_independent_poll"]

    @transaction.atomic()
    def create(self, validated_data):
        options_data = validated_data.pop("options", [])
        poll = super().create(validated_data)
        self._handle_options(poll, options_data)
        return poll

    @transaction.atomic()
    def update(self, instance, validated_data):
        options_data = validated_data.pop("options", [])
        poll = super().update(instance, validated_data)
        self._handle_options(poll, options_data)
        return poll

    def validate_options(self, data):
        for index, option_data in enumerate(data):
            pk = option_data.get("id")
            option_data["ordering"] = index + 1
            serializer_params = {"data": option_data}
            if pk:
                try:
                    option = self.instance.options.get(pk=pk)
                except SectionPollOption.DoesNotExist:
                    raise ValidationError(
                        "The Poll does not have an option with ID %s" % repr(pk)
                    )
                serializer_params["instance"] = option
            serializer = SectionPollOptionSerializer(**serializer_params)
            serializer.is_valid(raise_exception=True)
            # save serializer in data so it can be used when handling the options
            option_data["serializer"] = serializer
        return data

    def _handle_options(self, poll, data):
        new_option_ids = set()
        for option_data in data:
            serializer = option_data.pop("serializer")
            option = serializer.save(poll=poll, ordering=option_data["ordering"])
            new_option_ids.add(option.id)
        for option in poll.options.exclude(id__in=new_option_ids):
            option.soft_delete()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["options"] = SectionPollOptionSerializer(
            instance.options.all(), many=True
        ).data
        return data


def section_level_images_for(section):
    images = getattr(section, "section_level_images", None)
    if images is not None:
        return images
    return section.images.filter(purpose=SectionImage.PURPOSE_SECTION_LEVEL)


class SectionSerializer(serializers.ModelSerializer, TranslatableSerializer):
    """
    Serializer for section instance.
    """

    images = serializers.SerializerMethodField()
    files = SectionFileSerializer(many=True, read_only=True)
    questions = SectionPollSerializer(many=True, read_only=True, source="polls")
    type = serializers.SlugRelatedField(slug_field="identifier", read_only=True)
    type_name_singular = serializers.SlugRelatedField(
        source="type", slug_field="name_singular", read_only=True
    )
    type_name_plural = serializers.SlugRelatedField(
        source="type", slug_field="name_plural", read_only=True
    )
    commenting = EnumField(enum_type=Commenting)
    commenting_map_tools = EnumField(enum_type=CommentingMapTools)
    voting = EnumField(enum_type=Commenting)

    class Meta:
        model = Section
        fields = [
            "id",
            "type",
            "commenting",
            "commenting_map_tools",
            "voting",
            "title",
            "abstract",
            "content",
            "created_at",
            "images",
            "n_comments",
            "files",
            "questions",
            "type_name_singular",
            "type_name_plural",
            "plugin_identifier",
            "plugin_data",
            "plugin_fullscreen",
        ]

    @extend_schema_field(SectionImageSerializer(many=True))
    def get_images(self, instance):
        return SectionImageSerializer(
            section_level_images_for(instance),
            many=True,
            context=self.context,
        ).data


class SectionFieldSerializer(serializers.RelatedField):
    """
    Serializer for section field. A property of other instance.
    """

    def to_representation(self, section):
        return SectionSerializer(section, context=self.context).data


class SectionCreateUpdateSerializer(
    serializers.ModelSerializer, TranslatableSerializer
):
    """
    Serializer for section create/update.
    """

    id = serializers.CharField(required=False)
    type = serializers.SlugRelatedField(
        slug_field="identifier", queryset=SectionType.objects.all()
    )
    commenting = EnumField(enum_type=Commenting)
    voting = EnumField(enum_type=Commenting)
    commenting_map_tools = EnumField(enum_type=CommentingMapTools)

    # this field is used only for incoming data validation, outgoing data is added manually  # noqa: E501
    # in to_representation()
    images = serializers.ListField(child=serializers.DictField(), write_only=True)
    questions = serializers.ListField(
        child=serializers.DictField(), write_only=True, required=False
    )
    files = serializers.ListField(
        child=serializers.DictField(), write_only=True, required=False
    )

    class Meta:
        model = Section
        fields = [
            "id",
            "type",
            "commenting",
            "commenting_map_tools",
            "voting",
            "title",
            "abstract",
            "content",
            "plugin_identifier",
            "plugin_data",
            "images",
            "questions",
            "files",
            "ordering",
        ]

    @transaction.atomic()
    def save(self, **kwargs):
        section = super().save(**kwargs)
        self._handle_inline_images(
            section, self._get_inline_image_ids_from_content(section)
        )
        return section

    @transaction.atomic()
    def create(self, validated_data):
        images_data = validated_data.pop("images", [])
        polls_data = validated_data.pop("questions", [])
        files_data = validated_data.pop("files", [])
        section = super().create(validated_data)
        self._handle_images(section, images_data)
        self._handle_questions(section, polls_data)
        self._handle_files(section, files_data)
        return section

    @transaction.atomic()
    def update(self, instance, validated_data):
        images_data = validated_data.pop("images", [])
        polls_data = validated_data.pop("questions", [])
        files_data = validated_data.pop("files", [])
        section = super().update(instance, validated_data)
        self._handle_images(section, images_data)
        self._handle_questions(section, polls_data)
        self._handle_files(section, files_data)
        return section

    def validate_images(self, data):
        for index, image_data in enumerate(data):
            image_data["ordering"] = index

            image = None
            # NOTE: You can only use either pk or reference_id, not both. If you use both, pk will be used.  # noqa: E501
            # reference_id is meant for "save as new" type of situations. Not sure how it should behave if  # noqa: E501
            # used in conjunction with pk.
            if pk := image_data.get("id"):
                # Use an existing SectionImage.
                try:
                    # only allow orphan images or images within this section already
                    image = SectionImage.objects.filter(
                        Q(section=None) | Q(section=self.instance),
                        purpose=SectionImage.PURPOSE_SECTION_LEVEL,
                    ).get(pk=pk)
                except SectionImage.DoesNotExist:
                    raise ValidationError(
                        "No image with ID %s available in this section" % pk
                    )
                self._validate_orphan_image_access(image)
            elif reference_id := image_data.get("reference_id"):
                # Create a new SectionImage based on an existing image.
                try:
                    image = SectionImage.objects.get(
                        pk=reference_id,
                        purpose=SectionImage.PURPOSE_SECTION_LEVEL,
                    )
                except SectionImage.DoesNotExist:
                    raise ValidationError("Image %s does not exist" % reference_id)
                self._validate_orphan_image_access(image)
                image.pk = None

            serializer = SectionImageCreateUpdateSerializer(
                data=image_data, instance=image
            )
            serializer.is_valid(raise_exception=True)

            # save serializer in data, so it can be used when handling the images
            image_data["serializer"] = serializer

        return data

    def _validate_orphan_image_access(self, image):
        if image.section is not None:
            return

        if (request := self.context.get("request")) and (
            request.user.is_superuser
            or (
                request.user.is_authenticated and image.created_by_id == request.user.id
            )
        ):
            return

        raise ValidationError("You do not have access to this unattached image")

    def _create_inline_image_record(self, name, section):
        request = self.context.get("request")
        return SectionImage.objects.create(
            image=name,
            purpose=SectionImage.PURPOSE_INLINE,
            section=section,
            created_by=(
                request.user if request and request.user.is_authenticated else None
            ),
        )

    def validate_files(self, data):
        for index, file_data in enumerate(data):
            file_data["ordering"] = index

            file = None
            # NOTE: You can only use either pk or reference_id, not both. If you use both, pk will be used.  # noqa: E501
            # reference_id is meant for "save as new" type of situations. Not sure how it should behave if  # noqa: E501
            # used in conjunction with pk.
            if pk := file_data.get("id"):
                # Use an existing SectionFile.
                try:
                    # only allow orphan files or files within this section already
                    file = SectionFile.objects.filter(
                        Q(section=None) | Q(section=self.instance)
                    ).get(pk=pk)
                except SectionFile.DoesNotExist:
                    raise ValidationError(
                        "No file with ID %s available in this section" % pk
                    )
            elif reference_id := file_data.get("reference_id"):
                # Create a new SectionFile based on an existing file.
                try:
                    file = SectionFile.objects.get(pk=reference_id)
                except SectionFile.DoesNotExist:
                    raise ValidationError("File %s does not exist" % reference_id)
                file.pk = None

            serializer = RootFileBase64Serializer(
                data=file_data,
                instance=file,
                context={"request": self.context["request"]},
            )
            serializer.is_valid(raise_exception=True)

            # save serializer in data, so it can be used when handling the files
            file_data["serializer"] = serializer

        return data

    def _handle_images(self, section, data):
        new_image_ids = set()

        for image_data in data:
            serializer = image_data.pop("serializer")
            image = serializer.save(section=section)
            new_image_ids.add(image.id)

        for image in section.images.filter(
            purpose=SectionImage.PURPOSE_SECTION_LEVEL
        ).exclude(id__in=new_image_ids):
            image.soft_delete()

        return section

    def _handle_inline_images(self, section, image_ids):
        image_ids = set(image_ids)
        section.images.filter(purpose=SectionImage.PURPOSE_INLINE).exclude(
            id__in=image_ids
        ).update(
            deleted=True,
            deleted_at=now(),
        )
        SectionImage.objects.filter(
            pk__in=image_ids,
            purpose=SectionImage.PURPOSE_INLINE,
            section__isnull=True,
        ).update(section=section)

    def _find_matching_image(self, images, target_url):
        for image in images.order_by("-created_at", "-pk"):
            image_url = image.image.url
            if request := self.context.get("request"):
                image_url = request.build_absolute_uri(image_url)
            if image_url == target_url:
                return image
        return None

    def _get_inline_image_id_from_url(self, section, image_url):
        """Resolve an inline image URL to an inline image ID for the section."""
        inline_images = SectionImage.objects.filter(
            purpose=SectionImage.PURPOSE_INLINE,
            deleted=False,
        )
        # Prefer this section's existing instance before looking elsewhere.
        if matched_image := self._find_matching_image(
            inline_images.filter(section=section), image_url
        ):
            return matched_image.pk

        # Second, try an orphan owned by this user (or any orphan for a superuser).
        if (request := self.context.get("request")) and request.user.is_authenticated:
            orphan_images = inline_images.filter(section__isnull=True)
            if not request.user.is_superuser:
                orphan_images = orphan_images.filter(created_by=request.user)
            if matched_image := self._find_matching_image(orphan_images, image_url):
                self._validate_orphan_image_access(matched_image)
                return matched_image.pk

        # Third, if another section has this image, create a new instance for this
        # section rather than reassigning the existing instance. Can happen if a
        # section is copied, for example.
        if image_name := get_inline_image_name(image_url):
            other_images = inline_images.filter(
                section__isnull=False,
                image=image_name,
            ).exclude(section=section)
            if self._find_matching_image(other_images, image_url):
                new_image = self._create_inline_image_record(image_name, section)
                return new_image.pk

        return None

    def _get_inline_image_ids_from_content(self, section):
        image_urls = get_inline_image_urls(section.content_with_translations)
        image_ids = set()
        for image_url in image_urls:
            if image_url.lower().startswith("data:"):
                continue
            if request := self.context.get("request"):
                image_url = request.build_absolute_uri(image_url)
            if image_id := self._get_inline_image_id_from_url(section, image_url):
                image_ids.add(image_id)
            else:
                raise serializers.ValidationError(
                    "Inline images must be uploaded to this backend."
                )
        return image_ids

    def _handle_files(self, section, data):
        new_file_ids = set()

        for file_data in data:
            serializer = file_data.pop("serializer")
            file = serializer.save(section=section)
            new_file_ids.add(file.id)

        for file in section.files.exclude(id__in=new_file_ids):
            file.soft_delete()

        return section

    def _validate_question_update(self, poll_data, poll):
        poll_has_answers = poll.n_answers > 0
        if not poll_has_answers:
            return
        old_poll_data = SectionPollSerializer(poll).data
        text_unchanged = compare_serialized(old_poll_data["text"], poll_data["text"])
        options_unchanged = len(old_poll_data["options"]) == len(
            poll_data["options"]
        ) and all(
            compare_serialized(old_option["text"], option["text"])
            for old_option, option in zip(
                old_poll_data["options"], poll_data["options"]
            )
        )
        if not (text_unchanged and options_unchanged):
            raise ValidationError(
                "Poll with ID %s has answers - editing it is not allowed"
                % repr(poll.pk)
            )

    def validate_questions(self, data):
        for index, poll_data in enumerate(data):
            pk = poll_data.get("id")
            poll_data["ordering"] = index + 1
            serializer_params = {"data": poll_data}
            if pk:
                try:
                    poll = self.instance.polls.get(pk=pk)
                except SectionPoll.DoesNotExist:
                    raise ValidationError(
                        "The Section does not have a poll with ID %s" % repr(pk)
                    )
                self._validate_question_update(poll_data, poll)
                serializer_params["instance"] = poll
            serializer = SectionPollSerializer(**serializer_params)
            serializer.is_valid(raise_exception=True)
            # save serializer in data so it can be used when handling the polls
            poll_data["serializer"] = serializer
        return data

    def _handle_questions(self, section, data):
        new_poll_ids = set()
        for poll_data in data:
            serializer = poll_data.pop("serializer")
            poll = serializer.save(section=section, ordering=poll_data["ordering"])
            new_poll_ids.add(poll.id)
        for poll in section.polls.exclude(id__in=new_poll_ids):
            poll.soft_delete()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["images"] = SectionImageSerializer(
            section_level_images_for(instance),
            many=True,
            context=self.context,
        ).data
        data["questions"] = SectionPollSerializer(instance.polls.all(), many=True).data
        return data


@extend_schema_view(
    list=extend_schema(
        summary="List sections for a hearing",
        description=(
            "Retrieve all sections belonging to a specific hearing. "
            "Sections contain the content structure of a hearing."
        ),
    ),
    retrieve=extend_schema(
        summary="Get section details",
        description=(
            "Retrieve detailed information about a specific section within a hearing."
        ),
    ),
)
class SectionViewSet(AdminsSeeUnpublishedMixin, viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for hearing sections.

    Sections are the content blocks within a hearing. Each hearing has multiple sections
    that organize the content and can collect comments.
    """

    serializer_class = SectionSerializer
    model = Section

    @cached_property
    def hearing(self):
        id_or_slug = self.kwargs["hearing_pk"]
        return Hearing.objects.get_by_id_or_slug(id_or_slug)

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .filter(hearing=self.hearing)
            .select_related("type")
            .prefetch_related(
                "translations",
                Prefetch(
                    "polls",
                    SectionPoll.objects.prefetch_related(
                        "translations",
                        Prefetch(
                            "options",
                            SectionPollOption.objects.prefetch_related("translations"),
                        ),
                    ),
                ),
                Prefetch(
                    "images",
                    image_qs_for_request(self.request).prefetch_related("translations"),
                    to_attr="section_level_images",
                ),
                Prefetch(
                    "files",
                    file_qs_for_request(self.request).prefetch_related("translations"),
                ),
            )
        )
        if not self.hearing.closed:
            queryset = queryset.exclude(
                type__identifier=InitialSectionType.CLOSURE_INFO
            )
        return queryset


class RootSectionImageSerializer(
    ThumbnailImageSerializer, SectionImageCreateUpdateSerializer
):
    """
    Serializer for root level SectionImage endpoint /v1/image/
    """

    hearing = serializers.CharField(
        source="section.hearing_id", read_only=True, allow_null=True
    )
    purpose = serializers.ChoiceField(
        choices=SectionImage.PURPOSE_CHOICES,
        required=False,
        write_only=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and "section" in self.fields:
            self.fields["section"].required = False

    class Meta(SectionImageCreateUpdateSerializer.Meta):
        fields = SectionImageCreateUpdateSerializer.Meta.fields + [
            "id",
            "section",
            "hearing",
            "ordering",
            "purpose",
        ]

    @transaction.atomic()
    def create(self, validated_data):
        section_image = super().create(validated_data)
        self._update_ordering(section_image)
        return section_image

    @transaction.atomic()
    def update(self, instance, validated_data):
        is_section_changed = instance.section != validated_data.get(
            "section", instance.section
        )
        section_image = super().update(instance, validated_data)
        if is_section_changed:
            self._update_ordering(section_image)
        return section_image

    def _update_ordering(self, section_image):
        if not section_image.section:
            return

        existing_section_images = SectionImage.objects.filter(
            section=section_image.section,
            purpose=SectionImage.PURPOSE_SECTION_LEVEL,
        ).exclude(pk=section_image.pk)
        if existing_section_images.exists():
            section_image.ordering = (
                existing_section_images.aggregate(Max("ordering"))["ordering__max"] + 1
            )
        else:
            section_image.ordering = 1
        section_image.save()

    def to_internal_value(self, value):
        if (
            self.instance
            and "image" in value
            and self.get_url(self.instance) == value["image"]
        ):
            # do not try to save the local path in the field
            del value["image"]
        ret = super().to_internal_value(value)
        return ret


class RootSectionImageMultipartSerializer(RootSectionImageSerializer):
    image = serializers.ImageField(validators=[validate_image_size])


class ImageFilterSet(django_filters.rest_framework.FilterSet):
    hearing = django_filters.CharFilter(
        field_name="section__hearing__id",
        help_text="Filter by hearing ID",
    )
    section_type = django_filters.CharFilter(
        field_name="section__type__identifier",
        help_text="Filter by section type identifier",
    )

    class Meta:
        model = SectionImage
        fields = ["section", "hearing", "section_type"]


# root level SectionImage endpoint
@extend_schema_view(
    list=extend_schema(
        summary="List section images",
        description=(
            "Retrieve a paginated list of section-level images across all hearings. "
            "Results can be filtered by hearing, section, or section type."
        ),
        parameters=SECTION_IMAGE_PARAMS,
    ),
    retrieve=extend_schema(
        summary="Get section image details",
        description="Retrieve details of a specific section image.",
        parameters=DIM_PARAM,
    ),
    create=extend_schema(
        summary="Create section image",
        description=(
            "Upload a new image, optionally attached to a section. Supports "
            "multipart/form-data and base64 encoded images. Requires organization "
            "admin permissions. Set purpose to 'inline' for a WYSIWYG image; "
            "inline images are not included in section-level images."
        ),
        responses={
            201: RootSectionImageSerializer,
            403: OpenApiResponse(
                description="Only organization admin can create section images"
            ),
        },
    ),
    update=extend_schema(
        summary="Update section image",
        description=(
            "Update an existing section image. Requires organization admin permissions."
        ),
        responses={
            200: RootSectionImageSerializer,
            403: OpenApiResponse(
                description="Only organization admin can update section images"
            ),
        },
    ),
    partial_update=extend_schema(
        summary="Partially update section image",
        description=(
            "Partially update an existing section image. "
            "Requires organization admin permissions."
        ),
        responses={
            200: RootSectionImageSerializer,
            403: OpenApiResponse(
                description="Only organization admin can update section images"
            ),
        },
    ),
    destroy=extend_schema(
        summary="Delete section image",
        description=(
            "Soft delete a section image. Requires organization admin permissions."
        ),
        responses={
            204: OpenApiResponse(description="Image successfully deleted"),
            403: OpenApiResponse(
                description="Only organization admin can delete section images"
            ),
        },
    ),
)
class ImageViewSet(AdminsSeeUnpublishedMixin, AuditLogApiView, viewsets.ModelViewSet):
    """
    API endpoint for section images.

    Allows management of images attached to hearing sections. Supports both
    multipart and base64 encoded image uploads. Images support thumbnailing via
    the 'dim' query parameter.
    """

    model = SectionImage
    serializer_class = RootSectionImageSerializer
    pagination_class = DefaultLimitPagination
    filterset_class = ImageFilterSet
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_serializer_class(self):
        if "CONTENT_TYPE" in self.request.META and self.request.META[
            "CONTENT_TYPE"
        ].startswith("multipart"):
            return RootSectionImageMultipartSerializer
        return RootSectionImageSerializer

    def get_queryset(self):
        base_queryset = (
            super()
            .get_queryset()
            .select_related("section__hearing")
            .prefetch_related("translations")
        )
        queryset = filter_by_hearing_visible(
            base_queryset, self.request, "section__hearing"
        )
        if self.request.user.is_superuser:
            queryset = queryset | base_queryset.filter(section__isnull=True)
        elif self.request.user.is_authenticated:
            queryset = queryset | base_queryset.filter(
                section__isnull=True, created_by=self.request.user
            )
        if self.action == "list":
            queryset = queryset.filter(purpose=SectionImage.PURPOSE_SECTION_LEVEL)
        return queryset.filter(deleted=False)

    def _is_user_organisation_admin(self, user, section=None):
        if user.is_superuser:
            return True
        if section:
            target_org = section.hearing.organization
            return (
                target_org
                and user.admin_organizations.filter(id=target_org.id).exists()
            )
        return user.admin_organizations.exists()

    def _can_user_update_image(self, user, image, target_section):
        if image.section is None:
            if not (
                user.is_superuser
                or (user.is_authenticated and image.created_by_id == user.id)
            ):
                return False
        elif not self._is_user_organisation_admin(user, image.section):
            return False

        return target_section is None or self._is_user_organisation_admin(
            user, target_section
        )

    def _can_user_delete_image(self, user, image):
        if image.section is None:
            return user.is_superuser or (
                user.is_authenticated and image.created_by_id == user.id
            )
        return self._is_user_organisation_admin(user, image.section)

    def perform_create(self, serializer):
        if self._is_user_organisation_admin(
            self.request.user, serializer.validated_data.get("section")
        ):
            serializer.validated_data["created_by"] = self.request.user
            super().perform_create(serializer)
        else:
            raise PermissionDenied("Only organisation admin can create SectionImages")

    def perform_update(self, serializer):
        target_section = serializer.validated_data.get(
            "section", serializer.instance.section
        )
        if self._can_user_update_image(
            self.request.user, serializer.instance, target_section
        ):
            super().perform_update(serializer)
        else:
            raise PermissionDenied("Only organisation admin can update SectionImages")

    def perform_destroy(self, instance):
        if self._can_user_delete_image(self.request.user, instance):
            instance.soft_delete()
        else:
            raise PermissionDenied("Only organisation admin can delete SectionImages")


class RootFileSerializer(BaseFileSerializer, TranslatableSerializer):
    filetype = "sectionfile"
    hearing = serializers.CharField(
        source="section.hearing_id", read_only=True, allow_null=True
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # file content isn't mandatory on updates
        if self.instance:
            self.fields["file"].required = False

    class Meta:
        model = SectionFile
        fields = [
            "id",
            "title",
            "caption",
            "file",
            "ordering",
            "section",
            "hearing",
            "url",
        ]

    @transaction.atomic()
    def create(self, validated_data):
        section_file = super().create(validated_data)
        self._update_ordering(section_file)
        return section_file

    @transaction.atomic()
    def update(self, instance, validated_data):
        is_section_changed = instance.section != validated_data.get(
            "section", instance.section
        )
        section_file = super().update(instance, validated_data)
        if is_section_changed:
            self._update_ordering(section_file)
        return section_file

    def _update_ordering(self, section_file):
        existing_section_files = SectionFile.objects.filter(
            section=section_file.section
        ).exclude(pk=section_file.pk)
        if section_file.section and existing_section_files.exists():
            section_file.ordering = (
                existing_section_files.aggregate(Max("ordering"))["ordering__max"] + 1
            )
        else:
            section_file.ordering = 1
        section_file.save()

    def to_internal_value(self, value):
        if (
            self.instance
            and "file" in value
            and self.get_url(self.instance) == value["file"]
        ):
            # do not try to save the protected local path in the field
            del value["file"]
        ret = super().to_internal_value(value)
        return ret

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if "file" in ret:
            # do not return the protected local path
            ret["file"] = ret["url"]
        return ret


class RootFileBase64Serializer(RootFileSerializer):
    file = Base64FileField()


@extend_schema_view(
    list=extend_schema(
        summary="List section files",
        description="Retrieve paginated list of files attached to hearing sections.",
    ),
    retrieve=extend_schema(
        summary="Get section file details",
        description="Retrieve details of a specific section file.",
    ),
    create=extend_schema(
        summary="Upload section file",
        description=(
            "Upload a new file to a section. "
            "Supports both multipart/form-data and base64 encoded files. "
            "Requires organization admin permissions."
        ),
        responses={
            201: RootFileSerializer,
            403: OpenApiResponse(
                description="Only organization admin can create section files"
            ),
        },
    ),
    update=extend_schema(
        summary="Update section file",
        description=(
            "Update an existing section file. Requires organization admin permissions."
        ),
        responses={
            200: RootFileSerializer,
            403: OpenApiResponse(
                description="Only organization admin can update section files"
            ),
        },
    ),
    partial_update=extend_schema(
        summary="Partially update section file",
        description=(
            "Partially update an existing section file. "
            "Requires organization admin permissions."
        ),
        responses={
            200: RootFileSerializer,
            403: OpenApiResponse(
                description="Only organization admin can update section files"
            ),
        },
    ),
    destroy=extend_schema(
        summary="Delete section file",
        description=(
            "Soft delete a section file. Requires organization admin permissions."
        ),
        responses={
            204: OpenApiResponse(description="File successfully deleted"),
            403: OpenApiResponse(
                description="Only organization admin can delete section files"
            ),
        },
    ),
)
class FileViewSet(AdminsSeeUnpublishedMixin, AuditLogApiView, viewsets.ModelViewSet):
    """
    API endpoint for section files.

    Allows management of files (PDFs, documents, etc.) attached to hearing sections.
    Supports both multipart and base64 encoded file uploads.
    """

    model = SectionFile
    pagination_class = DefaultLimitPagination
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_serializer_class(self):
        if "CONTENT_TYPE" in self.request.META and self.request.META[
            "CONTENT_TYPE"
        ].startswith("multipart"):
            # multipart requests go to non-base64 serializer
            return RootFileSerializer
        return RootFileBase64Serializer

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .select_related("section")
            .prefetch_related("translations")
        )
        queryset = filter_by_hearing_visible(
            queryset, self.request, "section__hearing", include_orphans=True
        )
        return queryset.filter(deleted=False)

    def perform_create(self, serializer):
        if self._can_user_create(self.request.user, serializer):
            super().perform_create(serializer)
        else:
            raise PermissionDenied("Only organisation admin can create SectionFiles")

    def perform_update(self, serializer):
        if self._can_user_update(self.request.user, serializer):
            super().perform_update(serializer)
        else:
            raise PermissionDenied("Only organisation admin can update SectionFiles")

    def perform_destroy(self, instance):
        if self._can_user_destroy(self.request.user, instance):
            instance.soft_delete()
        else:
            raise PermissionDenied("Only organisation admin can delete SectionFiles")

    def _can_user_create(self, user, serializer):
        # new sectionless file can be created by any org admin
        # new file with section can be created if admin in that org
        section = serializer.validated_data.get("section")
        return self._is_user_organisation_admin(user, section)

    def _is_user_organisation_admin(self, user, section=None):
        if section:
            target_org = section.hearing.organization
            return (
                target_org
                and self.request.user.admin_organizations.filter(
                    id=target_org.id
                ).exists()
            )
        else:
            return self.request.user.admin_organizations.exists()

    def _can_user_update(self, user, serializer):
        # sectionless file can be edited without section data by any admin
        # sectionless file can be put to section if admin in that org
        # section file can be edited if admin in that org
        # section file can be put to another section if admin in both previous and
        # next org
        section = serializer.validated_data.get("section")
        instance = serializer.instance
        return self._is_user_organisation_admin(
            user, section
        ) and self._is_user_organisation_admin(user, instance.section)

    def _can_user_destroy(self, user, instance):
        # organisation admin can destroy a file with a section,
        # any organisation admin can destroy a sectionless file
        return self._is_user_organisation_admin(user, instance.section)


class RootSectionSerializer(SectionSerializer, TranslatableSerializer):
    """
    Serializer for root level section endpoint.
    """

    class Meta(SectionSerializer.Meta):
        fields = SectionSerializer.Meta.fields + ["hearing"]


class SectionFilterSet(django_filters.rest_framework.FilterSet):
    hearing = django_filters.CharFilter(
        field_name="hearing_id",
        help_text="Filter by hearing ID",
    )
    type = django_filters.CharFilter(
        field_name="type__identifier",
        help_text="Filter by section type identifier",
    )

    class Meta:
        model = Section
        fields = ["hearing", "type"]


def show_unpublished_for_request(request):
    return (
        request
        and request.user
        and request.user.is_authenticated
        and request.user.is_superuser
    )


def image_qs_for_request(request):
    queryset = SectionImage.objects.with_unpublished().filter(
        purpose=SectionImage.PURPOSE_SECTION_LEVEL
    )
    if show_unpublished_for_request(request):
        return queryset
    return queryset.filter(published=True)


def file_qs_for_request(request):
    if show_unpublished_for_request(request):
        return SectionFile.objects.with_unpublished()
    return SectionFile.objects.public()


# root level Section endpoint
@extend_schema_view(
    list=extend_schema(
        summary="List all sections",
        description=(
            "Retrieve paginated list of all sections across all hearings. "
            "Can be filtered by hearing or section type."
        ),
    ),
    retrieve=extend_schema(
        summary="Get section details",
        description="Retrieve detailed information about a specific section.",
    ),
)
class RootSectionViewSet(AdminsSeeUnpublishedMixin, viewsets.ReadOnlyModelViewSet):
    """
    Root-level API endpoint for sections across all hearings.

    Provides read-only access to all sections with filtering capabilities.
    """

    serializer_class = RootSectionSerializer
    model = Section
    pagination_class = DefaultLimitPagination
    filterset_class = SectionFilterSet

    def get_queryset(self):
        queryset = (
            super()
            .get_queryset()
            .select_related("type")
            .prefetch_related(
                "translations",
                "polls__translations",
                "polls__options__translations",
                Prefetch(
                    "images",
                    image_qs_for_request(self.request).prefetch_related("translations"),
                    to_attr="section_level_images",
                ),
                Prefetch(
                    "files",
                    file_qs_for_request(self.request).prefetch_related("translations"),
                ),
            )
        )
        queryset = filter_by_hearing_visible(queryset, self.request)

        n = now()
        open_hearings = (
            Q(hearing__force_closed=False)
            & Q(hearing__open_at__lte=n)
            & Q(hearing__close_at__gt=n)
        )
        queryset = queryset.exclude(
            open_hearings, type__identifier=InitialSectionType.CLOSURE_INFO
        )

        return queryset


class ServeFileView(View, SingleObjectMixin):
    def dispatch(self, request, *args, **kwargs):
        self.model = self.get_model(**kwargs)
        return super(ServeFileView, self).dispatch(request, *args, **kwargs)

    def get_model(self, **kwargs):
        filetype = kwargs.get("filetype", None)
        if filetype == "sectionimage":
            return SectionImage
        elif filetype == "sectionfile":
            return SectionFile
        raise ImproperlyConfigured("filetype url param is required")

    def get_queryset(self):
        queryset = super(ServeFileView, self).get_queryset()
        queryset = filter_by_hearing_visible(
            queryset, self.request, "section__hearing", include_orphans=True
        )
        return queryset.filter(deleted=False)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if isinstance(self.object, SectionImage):
            f = self.object.image
        elif isinstance(self.object, SectionFile):
            f = self.object.file
        return sendfile(request, f.path)
