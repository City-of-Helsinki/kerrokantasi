import django_filters
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.transaction import atomic
from django.utils.translation import ugettext as _
from rest_framework import filters, serializers
from rest_framework.exceptions import ValidationError
from rest_framework.fields import JSONField
from rest_framework.serializers import as_serializer_error
from rest_framework.settings import api_settings

from democracy.models import SectionComment, Label, Section
from democracy.models.section import CommentImage
from democracy.views.comment import COMMENT_FIELDS, BaseCommentViewSet, BaseCommentSerializer
from democracy.views.label import LabelSerializer
from democracy.pagination import DefaultLimitPagination
from democracy.views.comment_image import CommentImageCreateSerializer, CommentImageSerializer
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
                  'label', 'images', 'geojson', 'language_code']

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
                detail = as_serializer_error(ve)
                detail.setdefault("plugin_data", []).extend(detail.pop(api_settings.NON_FIELD_ERRORS_KEY, ()))
                raise ValidationError(detail=detail)
            attrs["plugin_identifier"] = section.plugin_identifier
        if not any([attrs.get(field) for field in SectionComment.fields_to_check_for_data]):
            raise ValidationError("You must supply at least one of the following data in a comment: " +
                                  str(SectionComment.fields_to_check_for_data))
        return attrs

    @atomic
    def save(self, **kwargs):
        user = self.context['request'].user
        if user and not user.is_anonymous and self.validated_data.get('author_name'):
            user.nickname = self.validated_data['author_name']
            user.save(update_fields=('nickname',))
        return super(SectionCommentCreateSerializer, self).save(**kwargs)

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
    images = CommentImageSerializer(many=True, read_only=True)

    class Meta:
        model = SectionComment
        fields = ['section', 'language_code'] + COMMENT_FIELDS


class SectionCommentViewSet(BaseCommentViewSet):
    model = SectionComment
    serializer_class = SectionCommentSerializer
    create_serializer_class = SectionCommentCreateSerializer
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter)
    ordering_fields = ('created_at', 'n_votes')


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
