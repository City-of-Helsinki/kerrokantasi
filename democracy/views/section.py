import django_filters
from django.db.models import Q, Max
from django.db import transaction
from django.utils.timezone import now
from easy_thumbnails.files import get_thumbnailer
from functools import lru_cache
from rest_framework import filters, serializers, viewsets, permissions
from rest_framework.exceptions import ValidationError, PermissionDenied, ParseError

from democracy.enums import Commenting, InitialSectionType
from democracy.models import Hearing, Section, SectionImage, SectionType
from democracy.pagination import DefaultLimitPagination
from democracy.utils.drf_enum_field import EnumField
from democracy.views.base import AdminsSeeUnpublishedMixin, BaseImageSerializer
from democracy.views.utils import (
    Base64ImageField, filter_by_hearing_visible, PublicFilteredImageField, TranslatableSerializer
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
        except:
            width = height = 0
        if not (width > 0 and height > 0):
            raise ValueError("width and height must be positive integers")
        # FIXME: Check allowed image dimensions better
        return (width, height)


class SectionImageSerializer(ThumbnailImageSerializer, TranslatableSerializer):
    class Meta:
        model = SectionImage
        fields = ['id', 'title', 'url', 'width', 'height', 'caption']


class SectionImageCreateUpdateSerializer(ThumbnailImageSerializer, TranslatableSerializer):
    image = Base64ImageField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # image content isn't mandatory on updates
        if self.instance:
            self.fields['image'].required = False

    class Meta:
        model = SectionImage
        fields = ['title', 'url', 'width', 'height', 'caption', 'image', 'ordering']


class SectionSerializer(serializers.ModelSerializer, TranslatableSerializer):
    """
    Serializer for section instance.
    """
    images = PublicFilteredImageField(serializer_class=SectionImageSerializer)
    type = serializers.SlugRelatedField(slug_field='identifier', read_only=True)
    type_name_singular = serializers.SlugRelatedField(source='type', slug_field='name_singular', read_only=True)
    type_name_plural = serializers.SlugRelatedField(source='type', slug_field='name_plural', read_only=True)
    commenting = EnumField(enum_type=Commenting)
    voting = EnumField(enum_type=Commenting)

    class Meta:
        model = Section
        fields = [
            'id', 'type', 'commenting', 'voting', 'published',
            'title', 'abstract', 'content', 'created_at', 'images', 'n_comments',
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

    # this field is used only for incoming data validation, outgoing data is added manually
    # in to_representation()
    images = serializers.ListField(child=serializers.DictField(), write_only=True)

    class Meta:
        model = Section
        fields = [
            'id', 'type', 'commenting', 'published',
            'title', 'abstract', 'content',
            'plugin_identifier', 'plugin_data',
            'images', 'ordering',
        ]

    @transaction.atomic()
    def create(self, validated_data):
        images_data = validated_data.pop('images', [])
        section = super().create(validated_data)
        self._handle_images(section, images_data)
        return section

    @transaction.atomic()
    def update(self, instance, validated_data):
        images_data = validated_data.pop('images', [])
        section = super().update(instance, validated_data)
        self._handle_images(section, images_data)
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

    def _handle_images(self, section, data):
        new_image_ids = set()

        for image_data in data:
            serializer = image_data.pop('serializer')
            image = serializer.save(section=section)
            new_image_ids.add(image.id)

        for image in section.images.exclude(id__in=new_image_ids):
            image.soft_delete()

        return section

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['images'] = SectionImageSerializer(
            instance.images.all(),
            many=True,
            context=self.context,
        ).data
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


class RootSectionImageSerializer(SectionImageCreateUpdateSerializer):
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


class ImageFilter(filters.FilterSet):
    hearing = django_filters.CharFilter(name='section__hearing__id')
    section_type = django_filters.CharFilter(name='section__type__identifier')

    class Meta:
        model = SectionImage
        fields = ['section', 'hearing', 'section_type']


# root level SectionImage endpoint
class ImageViewSet(AdminsSeeUnpublishedMixin, viewsets.ModelViewSet):
    model = SectionImage
    serializer_class = RootSectionImageSerializer
    pagination_class = DefaultLimitPagination
    filter_class = ImageFilter
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


class RootSectionSerializer(SectionSerializer, TranslatableSerializer):
    """
    Serializer for root level section endpoint.
    """

    class Meta(SectionSerializer.Meta):
        fields = SectionSerializer.Meta.fields + ['hearing']


class SectionFilter(filters.FilterSet):
    hearing = django_filters.CharFilter(name='hearing_id')
    type = django_filters.CharFilter(name='type__identifier')

    class Meta:
        model = Section
        fields = ['hearing', 'type']


# root level Section endpoint
class RootSectionViewSet(AdminsSeeUnpublishedMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = RootSectionSerializer
    model = Section
    pagination_class = DefaultLimitPagination
    filter_class = SectionFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = filter_by_hearing_visible(queryset, self.request)

        n = now()
        open_hearings = Q(hearing__force_closed=False) & Q(hearing__open_at__lte=n) & Q(hearing__close_at__gt=n)
        queryset = queryset.exclude(open_hearings, type__identifier=InitialSectionType.CLOSURE_INFO)

        return queryset
