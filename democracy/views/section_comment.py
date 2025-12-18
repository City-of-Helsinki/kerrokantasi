from urllib.parse import urljoin

import django_filters
from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.transaction import atomic
from django.utils.functional import cached_property
from django.utils.translation import gettext as _
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import filters, response, serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.relations import PrimaryKeyRelatedField
from rest_framework.serializers import as_serializer_error
from rest_framework.settings import api_settings

from democracy.enums import Commenting
from democracy.models import (
    Label,
    Section,
    SectionComment,
    SectionPoll,
    SectionPollAnswer,
    SectionPollOption,
)
from democracy.models.section import CommentImage
from democracy.pagination import DefaultLimitPagination
from democracy.views.comment import (
    COMMENT_FIELDS,
    BaseCommentSerializer,
    BaseCommentViewSet,
)
from democracy.views.comment_image import (
    CommentImageCreateSerializer,
    CommentImageSerializer,
)
from democracy.views.label import LabelSerializer
from democracy.views.openapi import (
    AUTHORIZATION_CODE_PARAM,
    COMMON_COMMENT_PARAMS,
    PAGINATION_PARAMS,
    ROOT_COMMENT_FILTER_PARAMS,
)
from democracy.views.utils import (
    GeoJSONField,
    GeometryBboxFilterBackend,
    NestedPKRelatedField,
    filter_by_hearing_visible,
    get_translation_list,
)


class SectionCommentCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for comments creation.
    """

    label = NestedPKRelatedField(
        queryset=Label.objects.all(),
        serializer=LabelSerializer,
        required=False,
        allow_null=True,
        expanded=True,
    )
    geojson = GeoJSONField(required=False, allow_null=True)
    images = CommentImageCreateSerializer(required=False, many=True)
    answers = (
        serializers.SerializerMethodField()
    )  # this makes the field read-only, create answers manually
    comment = serializers.PrimaryKeyRelatedField(
        queryset=SectionComment.objects.everything(), required=False, allow_null=True
    )

    class Meta:
        model = SectionComment
        fields = [
            "section",
            "comment",
            "content",
            "plugin_data",
            "authorization_code",
            "author_name",
            "label",
            "images",
            "answers",
            "geojson",
            "language_code",
            "pinned",
            "reply_to",
            "map_comment_text",
            "moderated",
            "edited",
        ]

    def get_answers(self, obj):
        polls_by_id = {}
        for answer in obj.poll_answers.select_related("option", "option__poll").all():
            if answer.option.poll.id not in polls_by_id:
                polls_by_id[answer.option.poll.id] = {
                    "question": answer.option.poll.id,
                    "type": answer.option.poll.type,
                    "answers": [],
                }
            polls_by_id[answer.option.poll.id]["answers"].append(answer.id)
        return list(polls_by_id.values())

    def to_internal_value(self, data):
        if data.get("plugin_data") is None:
            data["plugin_data"] = ""
        if data.get("images") is None:
            data["images"] = []
        return super().to_internal_value(data)

    def validate_section(self, value):
        if self.instance and value != self.instance.section:
            raise ValidationError(
                "Existing comment cannot be moved to a different section."
            )
        return value

    def validate_comment(self, value):
        if self.instance and value != self.instance.comment:
            raise ValidationError(
                "Existing comment cannot be changed to comment a different comment."
            )
        return value

    def validate_pinned(self, value):
        if value and (
            self.context["request"].user.is_anonymous
            or not self.context["request"].user.get_default_organization()
        ):
            raise ValidationError("Non-admin users may not pin their comments.")
        return value

    def validate(self, attrs):
        if attrs.get("plugin_data"):
            section = attrs["section"]
            try:
                if not section.plugin_identifier:
                    raise ValidationError(
                        "The section %s has no plugin; no plugin data is allowed."
                        % section
                    )
                plugin = section.plugin_implementation
                attrs["plugin_data"] = plugin.clean_client_data(attrs["plugin_data"])
            except (ValidationError, DjangoValidationError) as ve:
                # Massage the validation error slightly...
                detail = as_serializer_error(ve)
                detail.setdefault("plugin_data", []).extend(
                    detail.pop(api_settings.NON_FIELD_ERRORS_KEY, ())
                )
                raise ValidationError(detail=detail)
            attrs["plugin_identifier"] = section.plugin_identifier
        if not any(
            [attrs.get(field) for field in SectionComment.fields_to_check_for_data]
        ):
            raise ValidationError(
                "You must supply at least one of the following data in a comment: "
                + str(SectionComment.fields_to_check_for_data)
            )
        return attrs

    @atomic
    def save(self, *args, **kwargs):
        user = self.context["request"].user
        if user and not user.is_anonymous and self.validated_data.get("author_name"):
            user.nickname = self.validated_data["author_name"]
            user.save(update_fields=("nickname",))
        return super().save(*args, **kwargs)

    @atomic
    def create(self, validated_data):
        images = validated_data.pop("images", [])
        user = self.context["request"].user
        if user and not user.is_anonymous:
            validated_data["created_by_id"] = self.context["request"].user.id
        comment = SectionComment.objects.create(**validated_data)
        for image in images:
            CommentImage.objects.get_or_create(comment=comment, **image)
        return comment

    @atomic
    def update(self, instance, validated_data):
        images = validated_data.pop("images", [])
        # do not process extra fields created by rootsectioncommentserializer
        validated_data.pop("hearing_pk", None)
        validated_data.pop("comment_parent_pk", None)
        validated_data.pop("pk", None)
        instance = super().update(instance, validated_data)
        for image in images:
            CommentImage.objects.update(comment=instance, **image)
        return instance


class SectionCommentSerializer(BaseCommentSerializer):
    """
    Serializer for comment added to section.
    """

    section = PrimaryKeyRelatedField(
        queryset=Section.objects.all().prefetch_related(
            "translations",
            "hearing__translations",
        )
    )
    label = LabelSerializer(read_only=True)
    geojson = GeoJSONField(required=False, allow_null=True)
    images = CommentImageSerializer(many=True, read_only=True)
    answers = serializers.SerializerMethodField()
    creator_email = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()
    deleted_by_type = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField(allow_null=True)

    class Meta:
        model = SectionComment
        fields = [
            "section",
            "language_code",
            "answers",
            "comment",
            "comments",
            "n_comments",
            "pinned",
            "reply_to",
            "creator_email",
            "deleted",
            "deleted_at",
            "deleted_by_type",
            "can_delete",
            "can_edit",
        ] + COMMENT_FIELDS

    def get_content(self, obj):
        # Hide content if comment was deleted

        if not obj.deleted:
            return obj.content
        elif obj.deleted_by_id is not None and obj.deleted_by_id == obj.created_by_id:
            return "Kirjoittaja poisti oman viestinsä."
        elif obj.deleted_at:
            deleted_time = (
                f" {obj.deleted_at.strftime('%-d.%-m.%Y %H:%M')}"
                if obj.deleted_at is not None
                else ""
            )
            return (
                f"Viesti on poistettu{deleted_time}, koska se ei noudattanut Kerrokantasi-palvelun sääntöjä "  # noqa: E501
                f"{urljoin(settings.DEMOCRACY_UI_BASE_URL, '/info')}"
            )
        return "Viesti on poistettu."

    def get_answers(self, obj):
        polls_by_id = {}
        # poll_answers are prefetched in get_queryset
        for answer in obj.poll_answers.all():
            if answer.option.poll.id not in polls_by_id:
                polls_by_id[answer.option.poll.id] = {
                    "question": answer.option.poll.id,
                    "type": answer.option.poll.type,
                    "answers": [],
                }
            polls_by_id[answer.option.poll.id]["answers"].append(answer.option_id)
        return list(polls_by_id.values())

    def get_creator_email(self, obj):
        if not obj.deleted and obj.created_by and not obj.created_by.is_anonymous:
            return obj.created_by.email
        else:
            return ""

    def get_comments(self, obj):
        return [c.pk for c in obj.comments.all()]

    def get_deleted_by_type(self, obj):
        # Used to display a different message in the frontend if comment was
        # deleted by its creator

        if not obj.deleted:
            # Not deleted
            return None
        elif obj.deleted_by_id is not None and obj.deleted_by_id == obj.created_by_id:
            # Deleted by user themselves
            return "self"
        elif obj.deleted_by_id is not None and obj.deleted_at is not None:
            return "moderator"
        # No information about who deleted the comment
        return "unknown"

    @cached_property
    def request(self):
        return self.context.get("request")

    def get_can_edit(self, comment: SectionComment):
        return comment.can_edit(self.request)

    def get_can_delete(self, comment: SectionComment):
        return comment.can_delete(self.request)

    def to_representation(self, instance):
        if instance.deleted:
            instance.geojson = None

        data = super(SectionCommentSerializer, self).to_representation(instance)
        user_is_staff = (
            self.context["request"].user.is_staff
            or self.context["request"].user.is_superuser
        )

        if settings.HEARING_REPORT_PUBLIC_AUTHOR_NAMES and user_is_staff:
            return data
        else:
            del data["creator_email"]
            return data


@extend_schema_view(
    list=extend_schema(
        summary="List section comments",
        description=(
            "Retrieve paginated list of comments for hearing sections. "
            "Comments can be filtered and ordered."
        ),
        parameters=PAGINATION_PARAMS + COMMON_COMMENT_PARAMS,
    ),
    retrieve=extend_schema(
        summary="Get comment details",
        description="Retrieve detailed information about a specific comment.",
        parameters=AUTHORIZATION_CODE_PARAM,
    ),
    create=extend_schema(
        summary="Create comment",
        description=(
            "Post a new comment to a hearing section. "
            "Can include poll answers, images, and geographic data."
        ),
        responses={
            201: SectionCommentCreateUpdateSerializer,
            400: OpenApiResponse(
                description=(
                    "Validation error (e.g., commenting closed, invalid poll answer)"
                )
            ),
            403: OpenApiResponse(description="User not allowed to comment"),
        },
    ),
    update=extend_schema(
        summary="Update comment",
        description=(
            "Update an existing comment. Requires authorization code or ownership."
        ),
        responses={
            200: SectionCommentCreateUpdateSerializer,
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Not authorized to edit this comment"),
        },
    ),
    partial_update=extend_schema(
        summary="Partially update comment",
        description=(
            "Partially update an existing comment. "
            "Requires authorization code or ownership."
        ),
        responses={
            200: SectionCommentCreateUpdateSerializer,
            403: OpenApiResponse(description="Not authorized to edit this comment"),
        },
    ),
    destroy=extend_schema(
        summary="Delete comment",
        description="Soft delete a comment. Requires authorization code or ownership.",
        responses={
            204: OpenApiResponse(description="Comment successfully deleted"),
            403: OpenApiResponse(description="Not authorized to delete this comment"),
        },
    ),
)
class SectionCommentViewSet(BaseCommentViewSet):
    """
    API endpoint for section comments.

    Handles comments posted to hearing sections. Supports poll voting, image
    attachments, geographic data, and threaded replies. Comments can be
    moderated by organization admins.
    """

    model = SectionComment
    serializer_class = SectionCommentSerializer
    edit_serializer_class = SectionCommentCreateUpdateSerializer
    filter_backends = (
        django_filters.rest_framework.DjangoFilterBackend,
        filters.OrderingFilter,
        GeometryBboxFilterBackend,
    )
    ordering_fields = ("created_at", "n_votes")

    def _check_single_choice_poll(self, answer):
        if (
            len(answer["answers"]) > 1
            and SectionPoll.objects.get(id=answer["question"]).type
            == SectionPoll.TYPE_SINGLE_CHOICE
        ):
            raise ValidationError(
                {"answers": [_("A single choice poll may not have several answers.")]}
            )

    def _check_can_vote(self, answer):
        if not answer["answers"]:
            return None

        # Authenticated users can only have one answer per poll.
        if self.request.user.is_authenticated:
            poll_answers = SectionPollAnswer.objects.filter(
                option__poll=answer["question"], comment__created_by=self.request.user
            )
            if poll_answers:
                raise ValidationError({"answers": [_("You have already voted.")]})

    def create_related(self, request, instance=None):
        answers = request.data.pop("answers", [])
        for answer in answers:
            self._check_single_choice_poll(answer)
            self._check_can_vote(answer)

            for option_id in answer["answers"]:
                try:
                    option = SectionPollOption.objects.filter(
                        poll=answer["question"]
                    ).get(pk=option_id)
                    SectionPollAnswer.objects.create(comment=instance, option=option)
                except SectionPollOption.DoesNotExist:
                    raise ValidationError(
                        {
                            "option": [
                                _(
                                    'Invalid id "{id}" - option does not exist in this poll.'  # noqa: E501
                                ).format(id=option_id)
                            ]
                        }
                    )
        super().create_related(request, instance=instance)

    def update_related(self, request, instance=None):
        answers = request.data.pop("answers", [])
        for answer in answers:
            self._check_single_choice_poll(answer)

            option_ids = []
            for option_id in answer["answers"]:
                try:
                    option = SectionPollOption.objects.filter(
                        poll=answer["question"]
                    ).get(pk=option_id)
                    option_ids.append(option.pk)
                    if not SectionPollAnswer.objects.filter(
                        comment=instance, option=option
                    ).exists():
                        SectionPollAnswer.objects.create(
                            comment=instance, option=option
                        )
                except SectionPollOption.DoesNotExist:
                    raise ValidationError(
                        {
                            "option": [
                                _(
                                    'Invalid id "{id}" - option does not exist in this poll.'  # noqa: E501
                                ).format(id=option_id)
                            ]
                        }
                    )
            for section_poll_answer in SectionPollAnswer.objects.filter(
                option__poll=answer["question"], comment=instance
            ).exclude(option_id__in=option_ids):
                section_poll_answer.soft_delete()
        super().update_related(request, instance=instance)

    def get_comment_parent_id(self):
        """
        Given request, this method returns comment parent id, which can be indicated in an alarming number of ways
        due to the variety of the API endpoints and methods involved.
        """  # noqa: E501
        data = self.request.data
        params = self.request.query_params
        parent_id = None

        if "pk" in self.kwargs:
            # the parent id might be indicated by the direct URL
            comment_id = self.kwargs["pk"]
            parent_id = SectionComment.objects.everything().get(pk=comment_id).parent.id
        if not parent_id:
            # or the parent id might lurk in the nested URL
            parent_id = super().get_comment_parent_id()
        if not parent_id:
            # the comment parent id might lurk in the shadows of the section parameter
            # in the root endpoint
            parent_id = (
                data.get("section")
                if "section" in data and data["section"]
                else params.get("section", None)
            )
        if not parent_id:
            # the parent id might be found out from the parent of the original comment
            comment_id = data.get("comment") if "comment" in data else None
            if comment_id:
                parent_id = (
                    SectionComment.objects.everything().get(pk=comment_id).parent.id
                )

        return parent_id

    def get_comment_parent(self):
        parent_id = self.get_comment_parent_id()
        if not parent_id:
            return None

        try:
            return Section.objects.get(pk=parent_id)
        except Section.DoesNotExist:
            raise ValidationError(
                {
                    "section": [
                        _('Invalid pk "{pk_value}" - object does not exist.').format(
                            pk_value=parent_id
                        )
                    ]
                }
            )

    def _check_may_comment(self, request):
        parent = self.get_comment_parent()
        if not parent:
            # this should be possible only with POST requests
            raise ValidationError(
                {
                    "section": [
                        _(
                            "The comment section has to be specified in URL or by JSON section or comment field."  # noqa: E501
                        )
                    ]
                }
            )

        # Unauthenticated user can answer polls in hearings that have open commenting. The following if statement should  # noqa: E501
        # never be true as unauthenticated users can't post comments if the
        # hearing doesn't have open commenting.
        if (
            len(request.data.get("answers", [])) > 0
            and not request.user.is_authenticated
            and parent.commenting != Commenting.OPEN
        ):
            return response.Response(
                {
                    "status": "Unauthenticated users cannot answer polls in hearings that do not have open commenting."  # noqa: E501
                },
                status=status.HTTP_403_FORBIDDEN,
            )
        return super()._check_may_comment(request)


class RootSectionCommentSerializer(SectionCommentSerializer):
    """
    Serializer for root level comment endpoint /v1/comment/
    """

    hearing = serializers.CharField(source="section.hearing_id", read_only=True)
    hearing_data = serializers.SerializerMethodField()

    class Meta(SectionCommentSerializer.Meta):
        fields = SectionCommentSerializer.Meta.fields + ["hearing", "hearing_data"]

    def get_hearing_data(self, obj):
        """
        This is only used by comments on the profile page.
        Returns dict containing data from the hearing that the comment was made to.
        """
        request = self.context.get("request", None)
        user = request.user
        created_by_me = request.query_params.get("created_by", None)

        if created_by_me is not None and not user.is_anonymous:
            translations = {
                t.language_code: t.title
                for t in get_translation_list(obj.section.hearing)
            }

            return {
                "slug": obj.section.hearing.slug,
                "title": translations,
                "closed": obj.section.hearing.closed,
            }

        return False

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if self.context.get("remove_author_name"):
            ret["author_name"] = None
        return ret


class RootSectionCommentCreateUpdateSerializer(SectionCommentCreateUpdateSerializer):
    """
    Serializer for root level comment endpoint /v1/comment/
    """

    hearing = serializers.CharField(source="section.hearing_id", read_only=True)

    class Meta(SectionCommentSerializer.Meta):
        fields = SectionCommentCreateUpdateSerializer.Meta.fields + ["hearing"]


class CommentFilterSet(django_filters.rest_framework.FilterSet):
    hearing = django_filters.CharFilter(
        field_name="section__hearing__id",
        help_text="Filter by hearing ID",
    )
    label = django_filters.Filter(
        field_name="label__id",
        help_text="Filter by label ID",
    )
    created_at__lt = django_filters.IsoDateTimeFilter(
        field_name="created_at",
        lookup_expr="lt",
        help_text="Filter comments created before this date",
    )
    created_at__gt = django_filters.rest_framework.IsoDateTimeFilter(
        field_name="created_at",
        lookup_expr="gt",
        help_text="Filter comments created after this date",
    )
    comment = django_filters.ModelChoiceFilter(
        queryset=SectionComment.objects.everything(),
        help_text="Filter by parent comment ID",
    )
    section = django_filters.CharFilter(
        field_name="section__id",
        help_text="Filter by section ID",
    )
    created_by = django_filters.CharFilter(
        method="filter_created_by",
        help_text="Filter by creator ('me' for current user)",
    )

    class Meta:
        model = SectionComment
        fields = [
            "authorization_code",
            "created_at__lt",
            "created_at__gt",
            "section",
            "hearing",
            "label",
            "comment",
            "pinned",
        ]

    def filter_created_by(self, queryset, name, value: str):
        if value.lower() == "me" and not self.request.user.is_anonymous:
            return queryset.filter(created_by_id=self.request.user.id)

        return queryset.none()


# root level SectionComment endpoint
@extend_schema_view(
    list=extend_schema(
        summary="List all comments",
        description=(
            "Retrieve paginated list of comments across all hearings and sections. "
            "For privacy, author names are removed unless filtered by specific "
            "hearing, section, or user. Can be filtered and ordered."
        ),
        parameters=(
            PAGINATION_PARAMS + ROOT_COMMENT_FILTER_PARAMS + COMMON_COMMENT_PARAMS
        ),
    ),
    retrieve=extend_schema(
        summary="Get comment details",
        description="Retrieve detailed information about a specific comment.",
        parameters=AUTHORIZATION_CODE_PARAM,
    ),
    create=extend_schema(
        summary="Create comment (root endpoint)",
        description=(
            "Post a new comment to any hearing section. "
            "Can include poll answers, images, and geographic data. "
            "The section or comment to reply to must be specified in the request body."
        ),
        responses={
            201: RootSectionCommentCreateUpdateSerializer,
            400: OpenApiResponse(
                description=(
                    "Validation error (e.g., commenting closed, invalid poll answer, "
                    "section not specified)"
                )
            ),
            403: OpenApiResponse(description="User not allowed to comment"),
        },
    ),
    update=extend_schema(
        summary="Update comment (root endpoint)",
        description=(
            "Update an existing comment. Requires authorization code or ownership."
        ),
        responses={
            200: RootSectionCommentCreateUpdateSerializer,
            400: OpenApiResponse(description="Validation error"),
            403: OpenApiResponse(description="Not authorized to edit this comment"),
        },
    ),
    partial_update=extend_schema(
        summary="Partially update comment (root endpoint)",
        description=(
            "Partially update an existing comment. "
            "Requires authorization code or ownership."
        ),
        responses={
            200: RootSectionCommentCreateUpdateSerializer,
            403: OpenApiResponse(description="Not authorized to edit this comment"),
        },
    ),
    destroy=extend_schema(
        summary="Delete comment (root endpoint)",
        description="Soft delete a comment. Requires authorization code or ownership.",
        responses={
            204: OpenApiResponse(description="Comment successfully deleted"),
            403: OpenApiResponse(description="Not authorized to delete this comment"),
        },
    ),
)
class CommentViewSet(SectionCommentViewSet):
    """
    Root-level API endpoint for comments across all hearings.

    Provides access to all comments with extensive filtering capabilities.
    Author names are removed for privacy unless the query is filtered by
    specific hearing, section, or user.
    """

    serializer_class = RootSectionCommentSerializer
    edit_serializer_class = RootSectionCommentCreateUpdateSerializer
    pagination_class = DefaultLimitPagination
    filterset_class = CommentFilterSet

    @property
    def _is_filtered(self):
        """Is the queryset filtered enough to show author_names."""
        acceptable_filters = ["section", "hearing", "comment", "created_by"]
        filterset = self.filterset_class(
            data=self.request.query_params, request=self.request
        )
        if filterset.is_valid():
            for af in acceptable_filters:
                if filterset.form.cleaned_data[af]:
                    return True
        return False

    def get_serializer_context(self):
        """Author name will be removed for privacy reasons if fetching unfiltered comments."""  # noqa: E501
        context = super().get_serializer_context()

        if (
            self.action == "list"
            and not self._is_filtered
            and not bool(
                hasattr(self.request.user, "get_default_organization")
                and self.request.user.get_default_organization()
            )
        ):
            context["remove_author_name"] = True
        return context

    def get_queryset(self):
        """Returns all root-level comments, including deleted ones"""

        queryset = self.model.objects.everything()
        queryset = self.apply_select_and_prefetch(queryset)

        queryset = filter_by_hearing_visible(queryset, self.request, "section__hearing")

        user = self._get_user_from_request_or_context()
        if user.is_authenticated and user.is_superuser:
            return queryset
        else:
            return queryset.exclude(published=False)
