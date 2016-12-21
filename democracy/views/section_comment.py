import django_filters
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.transaction import atomic
from django.utils.translation import ugettext as _
from rest_framework import filters, serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import JSONField
from rest_framework.serializers import get_validation_error_detail
from rest_framework.settings import api_settings

from democracy.models import SectionComment, Label, Section
from democracy.models.section import CommentImage
from democracy.views.comment import COMMENT_FIELDS, BaseCommentViewSet, BaseCommentSerializer
from democracy.views.label import LabelSerializer
from democracy.views.section import SectionImageSerializer
from democracy.pagination import DefaultLimitPagination
from democracy.views.comment_image import CommentImageCreateSerializer
from democracy.views.utils import filter_by_hearing_visible, GeoJSONField, NestedPKRelatedField


class SectionCommentCreateSerializer(serializers.ModelSerializer):
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

    class Meta:
        model = SectionComment
        fields = ['section', 'content', 'plugin_data', 'authorization_code', 'author_name',
                  'label', 'images', 'geojson']

    def to_internal_value(self, data):
        if data.get("plugin_data") is None:
            data["plugin_data"] = ""
        if data.get("images") is None:
            data["images"] = []
        return super(SectionCommentCreateSerializer, self).to_internal_value(data)

    def validate(self, attrs):
        if attrs.get("plugin_data"):
            section = attrs["section"]
            try:
                if not section.plugin_identifier:
                    raise ValidationError("The section %s has no plugin; no plugin data is allowed." % section)
                plugin = section.plugin_implementation
                attrs["plugin_data"] = plugin.clean_client_data(attrs["plugin_data"])
            except (ValidationError, DjangoValidationError) as ve:
                # Massage the validation error slightly...
                detail = get_validation_error_detail(ve)
                detail.setdefault("plugin_data", []).extend(detail.pop(api_settings.NON_FIELD_ERRORS_KEY, ()))
                raise ValidationError(detail=detail)
            attrs["plugin_identifier"] = section.plugin_identifier
        if not (attrs.get("plugin_data") or attrs.get("content") or attrs.get("label")):
            raise ValidationError("Either content, plugin data or label must be supplied.")
        return attrs

    @atomic
    def create(self, validated_data):
        images = validated_data.pop('images', [])
        comment = SectionComment.objects.create(**validated_data)
        for image in images:
            CommentImage.objects.get_or_create(comment=comment, **image)
        return comment


class SectionCommentSerializer(BaseCommentSerializer):
    """
    Serializer for comment added to section.
    """
    label = LabelSerializer(read_only=True)
    geojson = JSONField(required=False, allow_null=True)
    images = SectionImageSerializer(many=True, read_only=True)

    class Meta:
        model = SectionComment
        fields = ['section'] + COMMENT_FIELDS


class SectionCommentViewSet(BaseCommentViewSet):
    model = SectionComment
    serializer_class = SectionCommentSerializer
    create_serializer_class = SectionCommentCreateSerializer


class RootSectionCommentSerializer(SectionCommentSerializer):
    """
    Serializer for root level comment endpoint /v1/comment/
    """
    hearing = serializers.CharField(source='section.hearing_id', read_only=True)

    class Meta(SectionCommentSerializer.Meta):
        fields = SectionCommentSerializer.Meta.fields + ['hearing']


class CommentFilter(filters.FilterSet):
    hearing = django_filters.CharFilter(name='section__hearing__id')

    class Meta:
        model = SectionComment
        fields = ['authorization_code', 'section', 'hearing']


# root level SectionComment endpoint
class CommentViewSet(SectionCommentViewSet):
    serializer_class = RootSectionCommentSerializer
    pagination_class = DefaultLimitPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = CommentFilter

    def get_comment_parent_id(self):
        method = self.request.method
        data = self.request.data

        if method == 'POST':
            return data.get('section') if 'section' in data else None
        elif method in ('PUT', 'PATCH'):
            return data.get('section') if 'section' in data else self.get_object().section_id
        elif method == 'DELETE':
            return self.get_object().section_id

        return None

    def get_comment_parent(self):
        parent_id = self.get_comment_parent_id()

        if not parent_id:
            return None

        try:
            return Section.objects.get(pk=parent_id)
        except Section.DoesNotExist:
            raise ValidationError({'section': [
                _('Invalid pk "{pk_value}" - object does not exist.').format(pk_value=parent_id)
            ]})

    def get_queryset(self):
        queryset = super(BaseCommentViewSet, self).get_queryset()
        queryset = filter_by_hearing_visible(queryset, self.request, 'section__hearing')
        return queryset

    def _check_may_comment(self, request):
        parent = self.get_comment_parent()
        if not parent:
            # this should be possible only with POST requests
            raise ValidationError({'section': [
                _('This field is required.')
            ]})
        return super(SectionCommentViewSet, self)._check_may_comment(request)
