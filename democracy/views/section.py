import django_filters
from django.db.models import Q, Max
from django.db import transaction
from django.utils.timezone import now
from django.views.generic import View
from django.views.generic.detail import SingleObjectMixin
from django.core.exceptions import ImproperlyConfigured
from easy_thumbnails.files import get_thumbnailer
from functools import lru_cache
from rest_framework import serializers, viewsets, permissions
from rest_framework.exceptions import ValidationError, PermissionDenied, ParseError
from sendfile import sendfile

from democracy.enums import Commenting, InitialSectionType, CommentingMapTools
from democracy.models import Hearing, Section, SectionImage, SectionType, SectionPoll, SectionPollOption, SectionFile
from democracy.pagination import DefaultLimitPagination
from democracy.utils.drf_enum_field import EnumField
from democracy.views.base import AdminsSeeUnpublishedMixin, BaseImageSerializer, BaseFileSerializer
from democracy.views.utils import (
    Base64ImageField, Base64FileField, filter_by_hearing_visible, PublicFilteredRelatedField, TranslatableSerializer,
    compare_serialized
)


class ThumbnailImageSerializer(BaseImageSerializer):
    """
    Image serializer supporting thumbnails via GET parameter

    ?dim=640x480
    """
    width = serializers.SerializerMethodField()
    height = serializers.SerializerMethodField()

    def get_width(self, obj):
        request = self._get_context_request()
        if request and 'dim' in request.GET:
            try:
                width, _height = self._parse_dimension_string(request.GET['dim'])
                return width
            except ValueError as verr:
                raise ParseError(detail=str(verr), code="invalid-dim-parameter")
        return obj.width

    def get_height(self, obj):
        request = self._get_context_request()
        if request and 'dim' in request.GET:
            try:
                _width, height = self._parse_dimension_string(request.GET['dim'])
                return height
            except ValueError as verr:
                raise ParseError(detail=str(verr), code="invalid-dim-parameter")
        return obj.height

    def _get_image(self, obj):
        request = self._get_context_request()
        if request and 'dim' in request.GET:
            try:
                width, height = self._parse_dimension_string(request.GET['dim'])
            except ValueError as verr:
                raise ParseError(detail=str(verr), code="invalid-dim-parameter")
            return get_thumbnailer(obj.image).get_thumbnail({
                'size': (width, height),
                'crop': 'smart',
            })
        else:
            return obj.image

    @lru_cache()
    def _parse_dimension_string(self, dim):
        """
        Parse a dimension string ("WxH") into (width, height).
        :param dim: Dimension string
        :type dim: str
        :return: Dimension tuple
        :rtype: tuple[int, int]
        """
        a = dim.split('x')
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
        # FIXME: Check allowed image dimensions better
        return (width, height)


class SectionImageSerializer(ThumbnailImageSerializer, TranslatableSerializer):
    class Meta:
        model = SectionImage
        fields = ['id', 'title', 'url', 'width', 'height', 'caption', 'alt_text']


class SectionImageCreateUpdateSerializer(BaseImageSerializer, TranslatableSerializer):
    image = Base64ImageField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # image content isn't mandatory on updates
        if self.instance:
            self.fields['image'].required = False

    class Meta:
        model = SectionImage
        fields = ['title', 'url', 'width', 'height', 'caption', 'alt_text', 'image', 'ordering']


class SectionFileSerializer(BaseFileSerializer, TranslatableSerializer):
    filetype = 'sectionfile'

    class Meta:
        model = SectionFile
        fields = ['id', 'title', 'url', 'caption']


class SectionPollOptionSerializer(serializers.ModelSerializer, TranslatableSerializer):
    class Meta:
        model = SectionPollOption
        fields = ['id', 'text', 'n_answers']


class SectionPollSerializer(serializers.ModelSerializer, TranslatableSerializer):
    options = serializers.ListField(child=serializers.DictField(), write_only=True)

    class Meta:
        model = SectionPoll
        fields = ['id', 'type', 'text', 'options', 'n_answers', 'is_independent_poll']

    @transaction.atomic()
    def create(self, validated_data):
        options_data = validated_data.pop('options', [])
        poll = super().create(validated_data)
        self._handle_options(poll, options_data)
        return poll

    @transaction.atomic()
    def update(self, instance, validated_data):
        options_data = validated_data.pop('options', [])
        poll = super().update(instance, validated_data)
        self._handle_options(poll, options_data)
        return poll

    def validate_options(self, data):
        for index, option_data in enumerate(data):
            pk = option_data.get('id')
            option_data['ordering'] = index + 1
            serializer_params = {'data': option_data}
            if pk:
                try:
                    option = self.instance.options.get(pk=pk)
                except SectionPollOption.DoesNotExist:
                    raise ValidationError('The Poll does not have an option with ID %s' % repr(pk))
                serializer_params['instance'] = option
            serializer = SectionPollOptionSerializer(**serializer_params)
            serializer.is_valid(raise_exception=True)
            # save serializer in data so it can be used when handling the options
            option_data['serializer'] = serializer
        return data

    def _handle_options(self, poll, data):
        new_option_ids = set()
        for option_data in data:
            serializer = option_data.pop('serializer')
            option = serializer.save(poll=poll, ordering=option_data['ordering'])
            new_option_ids.add(option.id)
        for option in poll.options.exclude(id__in=new_option_ids):
            option.soft_delete()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['options'] = SectionPollOptionSerializer(instance.options.all(), many=True).data
        return data


class SectionSerializer(serializers.ModelSerializer, TranslatableSerializer):
    """
    Serializer for section instance.
    """
    images = PublicFilteredRelatedField(serializer_class=SectionImageSerializer)
    files = PublicFilteredRelatedField(serializer_class=SectionFileSerializer)
    questions = SectionPollSerializer(many=True, read_only=True, source='polls')
    type = serializers.SlugRelatedField(slug_field='identifier', read_only=True)
    type_name_singular = serializers.SlugRelatedField(source='type', slug_field='name_singular', read_only=True)
    type_name_plural = serializers.SlugRelatedField(source='type', slug_field='name_plural', read_only=True)
    commenting = EnumField(enum_type=Commenting)
    commenting_map_tools = EnumField(enum_type=CommentingMapTools)
    voting = EnumField(enum_type=Commenting)

    class Meta:
        model = Section
        fields = [
            'id', 'type', 'commenting', 'commenting_map_tools', 'voting',
            'title', 'abstract', 'content', 'created_at', 'images', 'n_comments', 'files', 'questions',
            'type_name_singular', 'type_name_plural',
            'plugin_identifier', 'plugin_data', 'plugin_fullscreen',
        ]


class SectionFieldSerializer(serializers.RelatedField):
    """
    Serializer for section field. A property of other instance.
    """

    def to_representation(self, section):
        return SectionSerializer(section, context=self.context).data


class SectionCreateUpdateSerializer(serializers.ModelSerializer, TranslatableSerializer):
    """
    Serializer for section create/update.
    """
    id = serializers.CharField(required=False)
    type = serializers.SlugRelatedField(slug_field='identifier', queryset=SectionType.objects.all())
    commenting = EnumField(enum_type=Commenting)
    commenting_map_tools = EnumField(enum_type=CommentingMapTools)

    # this field is used only for incoming data validation, outgoing data is added manually
    # in to_representation()
    images = serializers.ListField(child=serializers.DictField(), write_only=True)
    questions = serializers.ListField(child=serializers.DictField(), write_only=True, required=False)
    files = serializers.ListField(child=serializers.DictField(), write_only=True, required=False)

    class Meta:
        model = Section
        fields = [
            'id', 'type', 'commenting', 'commenting_map_tools',
            'title', 'abstract', 'content',
            'plugin_identifier', 'plugin_data',
            'images', 'questions', 'files', 'ordering',
        ]

    @transaction.atomic()
    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        polls_data = validated_data.pop('questions', [])
        files_data = validated_data.pop('files', [])
        section = super().create(validated_data)
        self._handle_images(section, images_data)
        self._handle_questions(section, polls_data)
        self._handle_files(section, files_data)
        return section

    @transaction.atomic()
    def update(self, instance, validated_data):
        images_data = validated_data.pop('images', [])
        polls_data = validated_data.pop('questions', [])
        files_data = validated_data.pop('files', [])
        section = super().update(instance, validated_data)
        self._handle_images(section, images_data)
        self._handle_questions(section, polls_data)
        self._handle_files(section, files_data)
        return section

    def validate_images(self, data):
        for index, image_data in enumerate(data):
            pk = image_data.get('id')
            image_data['ordering'] = index
            serializer_params = {'data': image_data}

            if pk:
                try:
                    image = self.instance.images.get(pk=pk)
                except SectionImage.DoesNotExist:
                    raise ValidationError('The Section does not have an image with ID %s' % pk)

                serializer_params['instance'] = image

            serializer = SectionImageCreateUpdateSerializer(**serializer_params)
            serializer.is_valid(raise_exception=True)

            # save serializer in data so it can be used when handling the images
            image_data['serializer'] = serializer

        return data

    def validate_files(self, data):
        for index, file_data in enumerate(data):
            pk = file_data.get('id')
            file_data['ordering'] = index
            serializer_params = {
                'data': file_data,
                'context': {
                    'request': self.context['request']
                }
            }

            if pk:
                try:
                    # only allow orphan files or files within this section already
                    file = SectionFile.objects.filter(
                        Q(section=None) | (Q(section=self.instance))
                        ).get(pk=pk)
                except SectionImage.DoesNotExist:
                    raise ValidationError('No file with ID %s available in this section' % pk)

                serializer_params['instance'] = file

            serializer = RootFileBase64Serializer(**serializer_params)
            serializer.is_valid(raise_exception=True)

            # save serializer in data so it can be used when handling the files
            file_data['serializer'] = serializer

        return data

    def _handle_images(self, section, data):
        new_image_ids = set()

        for image_data in data:
            serializer = image_data.pop('serializer')
            image = serializer.save(section=section)
            new_image_ids.add(image.id)

        for image in section.images.exclude(id__in=new_image_ids):
            image.soft_delete()

        return section

    def _handle_files(self, section, data):
        new_file_ids = set()

        for file_data in data:
            serializer = file_data.pop('serializer')
            file = serializer.save(section=section)
            new_file_ids.add(file.id)

        for file in section.files.exclude(id__in=new_file_ids):
            file.soft_delete()

        return section

    def _validate_question_update(self, poll_data, poll):
        poll_has_answers = poll.n_answers > 0
        if not poll_has_answers:
            return
        try:
            old_poll_data = SectionPollSerializer(poll).data
            assert compare_serialized(old_poll_data['text'], poll_data['text'])
            assert len(old_poll_data['options']) == len(poll_data['options'])
            for old_option, option in zip(old_poll_data['options'], poll_data['options']):
                assert compare_serialized(old_option['text'], option['text'])
        except AssertionError:
            raise ValidationError('Poll with ID %s has answers - editing it is not allowed' % repr(poll.pk))

    def validate_questions(self, data):
        for index, poll_data in enumerate(data):
            pk = poll_data.get('id')
            poll_data['ordering'] = index + 1
            serializer_params = {'data': poll_data}
            if pk:
                try:
                    poll = self.instance.polls.get(pk=pk)
                except SectionPoll.DoesNotExist:
                    raise ValidationError('The Section does not have a poll with ID %s' % repr(pk))
                self._validate_question_update(poll_data, poll)
                serializer_params['instance'] = poll
            serializer = SectionPollSerializer(**serializer_params)
            serializer.is_valid(raise_exception=True)
            # save serializer in data so it can be used when handling the polls
            poll_data['serializer'] = serializer
        return data

    def _handle_questions(self, section, data):
        new_poll_ids = set()
        for poll_data in data:
            serializer = poll_data.pop('serializer')
            poll = serializer.save(section=section, ordering=poll_data['ordering'])
            new_poll_ids.add(poll.id)
        for poll in section.polls.exclude(id__in=new_poll_ids):
            poll.soft_delete()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['images'] = SectionImageSerializer(
            instance.images.all(),
            many=True,
            context=self.context,
        ).data
        data['questions'] = SectionPollSerializer(instance.polls.all(), many=True).data
        return data


class SectionViewSet(AdminsSeeUnpublishedMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = SectionSerializer
    model = Section

    def get_queryset(self):
        id_or_slug = self.kwargs['hearing_pk']
        hearing = Hearing.objects.get_by_id_or_slug(id_or_slug)
        queryset = super().get_queryset().filter(hearing=hearing)
        if not hearing.closed:
            queryset = queryset.exclude(type__identifier=InitialSectionType.CLOSURE_INFO)
        return queryset


class RootSectionImageSerializer(ThumbnailImageSerializer, SectionImageCreateUpdateSerializer):
    """
    Serializer for root level SectionImage endpoint /v1/image/
    """
    hearing = serializers.CharField(source='section.hearing_id', read_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            if 'section' in self.fields:
                self.fields['section'].required = False

    class Meta(SectionImageCreateUpdateSerializer.Meta):
        fields = SectionImageCreateUpdateSerializer.Meta.fields + ['id', 'section', 'hearing', 'ordering']

    @transaction.atomic()
    def create(self, validated_data):
        section_image = super().create(validated_data)
        section_images = section_image.section.images.all()
        if section_images.exists():
            section_image.ordering = section_images.aggregate(Max('ordering'))['ordering__max'] + 1
            section_image.save()
        return section_image

    def to_internal_value(self, value):
        if self.instance and 'image' in value and self.get_url(self.instance) == value['image']:
            # do not try to save the local path in the field
            del value['image']
        ret = super().to_internal_value(value)
        return ret


class ImageFilterSet(django_filters.rest_framework.FilterSet):
    hearing = django_filters.CharFilter(field_name='section__hearing__id')
    section_type = django_filters.CharFilter(field_name='section__type__identifier')

    class Meta:
        model = SectionImage
        fields = ['section', 'hearing', 'section_type']


# root level SectionImage endpoint
class ImageViewSet(AdminsSeeUnpublishedMixin, viewsets.ModelViewSet):
    model = SectionImage
    serializer_class = RootSectionImageSerializer
    pagination_class = DefaultLimitPagination
    filterset_class = ImageFilterSet
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = filter_by_hearing_visible(queryset, self.request, 'section__hearing')
        return queryset.filter(deleted=False)

    def _is_user_organisation_admin(self, section):
        target_org = section.hearing.organization
        return target_org and self.request.user.admin_organizations.filter(id=target_org.id).exists()

    def perform_create(self, serializer):
        if self._is_user_organisation_admin(serializer.validated_data['section']):
            return super().perform_create(serializer)
        else:
            raise PermissionDenied('Only organisation admin can create SectionImages')

    def perform_update(self, serializer):
        if self._is_user_organisation_admin(serializer.instance.section):
            return super().perform_update(serializer)
        else:
            raise PermissionDenied('Only organisation admin can update SectionImages')

    def perform_destroy(self, instance):
        if self._is_user_organisation_admin(instance.section):
            instance.soft_delete()
        else:
            raise PermissionDenied('Only organisation admin can delete SectionImages')


class RootFileSerializer(BaseFileSerializer, TranslatableSerializer):
    filetype = 'sectionfile'
    hearing = serializers.CharField(source='section.hearing_id', read_only=True, allow_null=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # file content isn't mandatory on updates
        if self.instance:
            self.fields['file'].required = False

    class Meta:
        model = SectionFile
        fields = ['id', 'title', 'caption', 'file', 'ordering', 'section', 'hearing', 'url']

    @transaction.atomic()
    def create(self, validated_data):
        section_file = super().create(validated_data)
        self._update_ordering(section_file)
        return section_file

    @transaction.atomic()
    def update(self, instance, validated_data):
        is_section_changed = instance.section != validated_data.get('section', instance.section)
        section_file = super().update(instance, validated_data)
        if is_section_changed:
            self._update_ordering(section_file)
        return section_file

    def _update_ordering(self, section_file):
        existing_section_files = SectionFile.objects.filter(section=section_file.section).exclude(pk=section_file.pk)
        if section_file.section and existing_section_files.exists():
            section_file.ordering = existing_section_files.aggregate(Max('ordering'))['ordering__max'] + 1
        else:
            section_file.ordering = 1
        section_file.save()

    def to_internal_value(self, value):
        if self.instance and 'file' in value and self.get_url(self.instance) == value['file']:
            # do not try to save the protected local path in the field
            del value['file']
        ret = super().to_internal_value(value)
        return ret

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        if 'file' in ret:
            # do not return the protected local path
            ret['file'] = ret['url']
        return ret


class RootFileBase64Serializer(RootFileSerializer):
    file = Base64FileField()


class FileViewSet(AdminsSeeUnpublishedMixin, viewsets.ModelViewSet):
    model = SectionFile
    pagination_class = DefaultLimitPagination
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def get_serializer_class(self):
        if (self.request.META['CONTENT_TYPE'].startswith('multipart')):
            # multipart requests go to non-base64 serializer
            return RootFileSerializer
        return RootFileBase64Serializer

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = filter_by_hearing_visible(queryset, self.request, 'section__hearing', include_orphans=True)
        return queryset.filter(deleted=False)

    def perform_create(self, serializer):
        if self._can_user_create(self.request.user, serializer):
            return super().perform_create(serializer)
        else:
            raise PermissionDenied('Only organisation admin can create SectionFiles')

    def perform_update(self, serializer):
        if self._can_user_update(self.request.user, serializer):
            return super().perform_update(serializer)
        else:
            raise PermissionDenied('Only organisation admin can update SectionFiles')

    def perform_destroy(self, instance):
        if self._can_user_destroy(self.request.user, instance):
            instance.soft_delete()
        else:
            raise PermissionDenied('Only organisation admin can delete SectionFiles')

    def _can_user_create(self, user, serializer):
        # new sectionless file can be created by any org admin
        # new file with section can be created if admin in that org
        section = serializer.validated_data.get('section')
        return self._is_user_organisation_admin(user, section)

    def _is_user_organisation_admin(self, user, section=None):
        if section:
            target_org = section.hearing.organization
            return target_org and self.request.user.admin_organizations.filter(id=target_org.id).exists()
        else:
            return self.request.user.admin_organizations.exists()

    def _can_user_update(self, user, serializer):
        # sectionless file can be edited without section data by any admin
        # sectionless file can be put to section if admin in that org
        # section file can be edited if admin in that org
        # section file can be put to another section if admin in both previous and next org
        section = serializer.validated_data.get('section')
        instance = serializer.instance
        return (
            self._is_user_organisation_admin(user, section) and
            self._is_user_organisation_admin(user, instance.section)
        )

    def _can_user_destroy(self, user, instance):
        # organisation admin can destroy a file with a section,
        # any organisation admin can destroy a sectionless file
        return self._is_user_organisation_admin(user, instance.section)


class RootSectionSerializer(SectionSerializer, TranslatableSerializer):
    """
    Serializer for root level section endpoint.
    """

    class Meta(SectionSerializer.Meta):
        fields = SectionSerializer.Meta.fields + ['hearing']


class SectionFilterSet(django_filters.rest_framework.FilterSet):
    hearing = django_filters.CharFilter(field_name='hearing_id')
    type = django_filters.CharFilter(field_name='type__identifier')

    class Meta:
        model = Section
        fields = ['hearing', 'type']


# root level Section endpoint
class RootSectionViewSet(AdminsSeeUnpublishedMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = RootSectionSerializer
    model = Section
    pagination_class = DefaultLimitPagination
    filterset_class = SectionFilterSet

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = filter_by_hearing_visible(queryset, self.request)

        n = now()
        open_hearings = Q(hearing__force_closed=False) & Q(hearing__open_at__lte=n) & Q(hearing__close_at__gt=n)
        queryset = queryset.exclude(open_hearings, type__identifier=InitialSectionType.CLOSURE_INFO)

        return queryset


class ServeFileView(View, SingleObjectMixin):
    def dispatch(self, request, *args, **kwargs):
        self.model = self.get_model(request, *args, **kwargs)
        return super(ServeFileView, self).dispatch(request, *args, **kwargs)

    def get_model(self, request, *args, **kwargs):
        filetype = kwargs.get('filetype', None)
        if filetype == 'sectionimage':
            return SectionImage
        elif filetype == 'sectionfile':
            return SectionFile
        raise ImproperlyConfigured('filetype url param is required')

    def get_queryset(self):
        queryset = super(ServeFileView, self).get_queryset()
        queryset = filter_by_hearing_visible(queryset, self.request, 'section__hearing', include_orphans=True)
        return queryset.filter(deleted=False)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        if isinstance(self.object, SectionImage):
            f = self.object.image
        elif isinstance(self.object, SectionFile):
            f = self.object.file
        return sendfile(request, f.path)
