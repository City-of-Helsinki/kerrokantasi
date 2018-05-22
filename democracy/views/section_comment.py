import django_filters
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.transaction import atomic
from django.utils.translation import ugettext as _
from rest_framework import filters, serializers, status, response
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import as_serializer_error
from rest_framework.settings import api_settings

from democracy.models import SectionComment, Label, Section, SectionPollOption, SectionPollAnswer
from democracy.models.section import CommentImage
from democracy.views.comment import COMMENT_FIELDS, BaseCommentViewSet, BaseCommentSerializer
from democracy.views.label import LabelSerializer
from democracy.pagination import DefaultLimitPagination
from democracy.views.comment_image import CommentImageCreateSerializer, CommentImageSerializer
from democracy.views.utils import filter_by_hearing_visible, NestedPKRelatedField
from democracy.views.utils import GeoJSONField, GeometryBboxFilterBackend


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
    answers = serializers.SerializerMethodField()

    class Meta:
        model = SectionComment
        fields = ['section', 'content', 'plugin_data', 'authorization_code', 'author_name',
                  'label', 'images', 'answers', 'geojson', 'language_code']

    def get_answers(self, obj):
        polls_by_id = {}
        for answer in obj.poll_answers.select_related('option', 'option__poll').all():
            if answer.option.poll.id not in polls_by_id:
                polls_by_id[answer.option.poll.id] = {
                    'question': answer.option.poll.id,
                    'type': answer.option.poll.type,
                    'answers': [],
                }
            polls_by_id[answer.option.poll.id]['answers'].append(answer.id)
        return list(polls_by_id.values())

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
        if user and not user.is_anonymous() and self.validated_data.get('author_name'):
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
    geojson = GeoJSONField(required=False, allow_null=True)
    images = CommentImageSerializer(many=True, read_only=True)
    answers = serializers.SerializerMethodField()

    class Meta:
        model = SectionComment
        fields = ['section', 'language_code', 'answers'] + COMMENT_FIELDS

    def get_answers(self, obj):
        polls_by_id = {}
        for answer in obj.poll_answers.select_related('option', 'option__poll').all():
            if answer.option.poll.id not in polls_by_id:
                polls_by_id[answer.option.poll.id] = {
                    'question': answer.option.poll.id,
                    'type': answer.option.poll.type,
                    'answers': [],
                }
            polls_by_id[answer.option.poll.id]['answers'].append(answer.option_id)
        return list(polls_by_id.values())


class SectionCommentViewSet(BaseCommentViewSet):
    model = SectionComment
    serializer_class = SectionCommentSerializer
    create_serializer_class = SectionCommentCreateSerializer
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter, GeometryBboxFilterBackend)
    ordering_fields = ('created_at', 'n_votes')

    def create_related(self, request, instance=None, *args, **kwargs):
        answers = request.data.pop('answers', [])
        for answer in answers:
            for option_id in answer['answers']:
                try:
                    option = SectionPollOption.objects.get(pk=option_id)
                    SectionPollAnswer.objects.create(comment=instance, option=option)
                except SectionPollOption.DoesNotExist:
                    raise ValidationError({'option': [
                        _('Invalid id "{id}" - object does not exist.').format(id=option_id)
                    ]})
        super().create_related(request, instance=instance, *args, **kwargs)

    def update_related(self, request, instance=None, *args, **kwargs):
        answers = request.data.pop('answers', [])
        for answer in answers:
            option_ids = []
            for option_id in answer['answers']:
                try:
                    option = SectionPollOption.objects.get(pk=option_id)
                    option_ids.append(option.pk)
                    if not SectionPollAnswer.objects.filter(comment=instance, option=option).exists():
                        SectionPollAnswer.objects.create(comment=instance, option=option)
                except SectionPollOption.DoesNotExist:
                    raise ValidationError({'option': [
                        _('Invalid id "{id}" - object does not exist.').format(id=option_id)
                    ]})
            for answer in SectionPollAnswer.objects.filter(comment=instance).exclude(option_id__in=option_ids):
                answer.soft_delete()
        super().update_related(request, instance=instance, *args, **kwargs)

    def _check_may_comment(self, request):
        if len(request.data.get('answers', [])) > 0 and not request.user.is_authenticated():
            return response.Response(
                {'status': 'Unauthenticated users cannot answer polls.'},
                status=status.HTTP_403_FORBIDDEN
            )
        return super()._check_may_comment(request)


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
