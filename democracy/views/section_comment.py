import django_filters
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.transaction import atomic
from django.utils.translation import ugettext as _
from rest_framework import filters, serializers, status, response
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import as_serializer_error
from rest_framework.settings import api_settings

from democracy.models import SectionComment, Label, Section, SectionPoll, SectionPollOption, SectionPollAnswer
from democracy.models.section import CommentImage
from democracy.views.comment import COMMENT_FIELDS, BaseCommentViewSet, BaseCommentSerializer
from democracy.views.label import LabelSerializer
from democracy.pagination import DefaultLimitPagination
from democracy.views.comment_image import CommentImageCreateSerializer, CommentImageSerializer
from democracy.views.utils import filter_by_hearing_visible, NestedPKRelatedField
from democracy.views.utils import GeoJSONField, GeometryBboxFilterBackend


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
    answers = serializers.SerializerMethodField()  # this makes the field read-only, create answers manually

    class Meta:
        model = SectionComment
        fields = ['section', 'comment', 'content', 'plugin_data', 'authorization_code', 'author_name',
                  'label', 'images', 'answers', 'geojson', 'language_code', 'pinned', 'reply_to', 'map_comment_text']

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
        return super().to_internal_value(data)

    def validate_section(self, value):
        if self.instance and value != self.instance.section:
            raise ValidationError("Existing comment cannot be moved to a different section.")
        return value

    def validate_comment(self, value):
        if self.instance and value != self.instance.comment:
            raise ValidationError("Existing comment cannot be changed to comment a different comment.")
        return value

    def validate_pinned(self, value):
        if value and (self.context['request'].user.is_anonymous or
                      not self.context['request'].user.get_default_organization()):
            raise ValidationError("Non-admin users may not pin their comments.")
        return value

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
    def save(self, *args, **kwargs):
        user = self.context['request'].user
        if user and not user.is_anonymous and self.validated_data.get('author_name'):
            user.nickname = self.validated_data['author_name']
            user.save(update_fields=('nickname',))
        return super().save(*args, **kwargs)

    @atomic
    def create(self, validated_data):
        images = validated_data.pop('images', [])
        comment = SectionComment.objects.create(**validated_data)
        for image in images:
            CommentImage.objects.get_or_create(comment=comment, **image)
        return comment

    @atomic
    def update(self, instance, validated_data):
        images = validated_data.pop('images', [])
        # do not process extra fields created by rootsectioncommentserializer
        validated_data.pop('hearing_pk', None)
        validated_data.pop('comment_parent_pk', None)
        validated_data.pop('pk', None)
        instance = super().update(instance, validated_data)
        for image in images:
            CommentImage.objects.update(comment=instance, **image)
        return instance


class SectionCommentSerializer(BaseCommentSerializer):
    """
    Serializer for comment added to section.
    """
    label = LabelSerializer(read_only=True)
    geojson = GeoJSONField(required=False, allow_null=True)
    images = CommentImageSerializer(many=True, read_only=True)
    answers = serializers.SerializerMethodField()
    creator_name = serializers.SerializerMethodField()

    class Meta:
        model = SectionComment        
        fields = ['section', 'language_code', 'answers', 'comment',
                  'comments', 'n_comments', 'pinned', 'reply_to', 'creator_name'] + COMMENT_FIELDS

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

    def get_creator_name(self, obj):
        if obj.created_by and not obj.created_by.is_anonymous:
            return obj.created_by.get_full_name()
        else:
            return 'Anonymous'
    
    def to_representation(self, instance):
        data = super(SectionCommentSerializer, self).to_representation(instance)
        if not self.context['request'].user.is_staff and not self.context['request'].user.is_superuser:
            del data['creator_name']

        return data

class SectionCommentViewSet(BaseCommentViewSet):
    model = SectionComment
    serializer_class = SectionCommentSerializer
    edit_serializer_class = SectionCommentCreateUpdateSerializer
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,
                       filters.OrderingFilter,
                       GeometryBboxFilterBackend)
    ordering_fields = ('created_at', 'n_votes')

    def _check_single_choice_poll(self, answer):
        if (len(answer['answers']) > 1 and
                SectionPoll.objects.get(id=answer['question']).type == SectionPoll.TYPE_SINGLE_CHOICE):
            raise ValidationError({'answers': [_('A single choice poll may not have several answers.')]})

    def _check_can_vote(self, answer):
        if not answer['answers']:
            return None
        poll_answers = SectionPollAnswer.objects.filter(
            option__poll=answer['question'],
            comment__created_by=self.request.user
        )
        if poll_answers:
            raise ValidationError({'answers': [_('You have already voted.')]})

    def create_related(self, request, instance=None, *args, **kwargs):
        answers = request.data.pop('answers', [])
        for answer in answers:
            self._check_single_choice_poll(answer)
            self._check_can_vote(answer)

            for option_id in answer['answers']:
                try:
                    option = SectionPollOption.objects.filter(poll=answer['question']).get(pk=option_id)
                    SectionPollAnswer.objects.create(comment=instance, option=option)
                except SectionPollOption.DoesNotExist:
                    raise ValidationError({'option': [
                        _('Invalid id "{id}" - option does not exist in this poll.').format(id=option_id)
                    ]})
        super().create_related(request, instance=instance, *args, **kwargs)

    def update_related(self, request, instance=None, *args, **kwargs):
        answers = request.data.pop('answers', [])
        for answer in answers:
            self._check_single_choice_poll(answer)

            option_ids = []
            for option_id in answer['answers']:
                try:
                    option = SectionPollOption.objects.filter(poll=answer['question']).get(pk=option_id)
                    option_ids.append(option.pk)
                    if not SectionPollAnswer.objects.filter(comment=instance, option=option).exists():
                        SectionPollAnswer.objects.create(comment=instance, option=option)
                except SectionPollOption.DoesNotExist:
                    raise ValidationError({'option': [
                        _('Invalid id "{id}" - option does not exist in this poll.').format(id=option_id)
                    ]})
            for answer in SectionPollAnswer.objects.filter(
                    option__poll=answer['question'],
                    comment=instance
                    ).exclude(option_id__in=option_ids):
                answer.soft_delete()
        super().update_related(request, instance=instance, *args, **kwargs)

    def get_comment_parent_id(self):
        """
        Given request, this method returns comment parent id, which can be indicated in an alarming number of ways
        due to the variety of the API endpoints and methods involved.
        """
        data = self.request.data
        params = self.request.query_params
        parent_id = None

        if 'pk' in self.kwargs:
            # the parent id might be indicated by the direct URL
            comment_id = self.kwargs["pk"]
            parent_id = SectionComment.objects.get(pk=comment_id).parent.id
        if not parent_id:
            # or the parent id might lurk in the nested URL
            parent_id = super().get_comment_parent_id()
        if not parent_id:
            # the comment parent id might lurk in the shadows of the section parameter in the root endpoint
            parent_id = data.get('section') if 'section' in data and data['section'] else params.get('section', None)
        if not parent_id:
            # the parent id might be found out from the parent of the original comment
            comment_id = data.get('comment') if 'comment' in data else None
            if comment_id:
                parent_id = SectionComment.objects.get(pk=comment_id).parent.id

        return parent_id

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

    def _check_may_comment(self, request):
        parent = self.get_comment_parent()
        if not parent:
            # this should be possible only with POST requests
            raise ValidationError({'section': [
                _('The comment section has to be specified in URL or by JSON section or comment field.')
            ]})
        if len(request.data.get('answers', [])) > 0 and not request.user.is_authenticated:
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


class RootSectionCommentCreateUpdateSerializer(SectionCommentCreateUpdateSerializer):
    """
    Serializer for root level comment endpoint /v1/comment/
    """
    hearing = serializers.CharField(source='section.hearing_id', read_only=True)

    class Meta(SectionCommentSerializer.Meta):
        fields = SectionCommentCreateUpdateSerializer.Meta.fields + ['hearing']


class CommentFilterSet(django_filters.rest_framework.FilterSet):
    hearing = django_filters.CharFilter(field_name='section__hearing__id')
    label = django_filters.Filter(field_name='label__id')
    created_at__lt = django_filters.IsoDateTimeFilter(field_name='created_at', lookup_expr='lt')
    created_at__gt = django_filters.rest_framework.IsoDateTimeFilter(field_name='created_at', lookup_expr='gt')

    class Meta:
        model = SectionComment
        fields = ['authorization_code', 'created_at__lt', 'created_at__gt', 'section',
                  'hearing', 'label', 'comment', 'pinned']


# root level SectionComment endpoint
class CommentViewSet(SectionCommentViewSet):
    serializer_class = RootSectionCommentSerializer
    edit_serializer_class = RootSectionCommentCreateUpdateSerializer
    pagination_class = DefaultLimitPagination
    filterset_class = CommentFilterSet

    def get_queryset(self):
        queryset = super(BaseCommentViewSet, self).get_queryset()
        queryset = filter_by_hearing_visible(queryset, self.request, 'section__hearing')
        return queryset
