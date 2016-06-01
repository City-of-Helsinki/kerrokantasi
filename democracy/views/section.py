import django_filters
from django.db.models import Q
from django.utils.timezone import now
from rest_framework import filters, serializers, viewsets
from rest_framework.pagination import LimitOffsetPagination

from democracy.enums import Commenting, InitialSectionType
from democracy.models import Hearing, Section, SectionImage
from democracy.utils.drf_enum_field import EnumField
from democracy.views.base import AdminsSeeUnpublishedMixin, BaseImageSerializer
from democracy.views.utils import filter_by_hearing_visible, PublicFilteredImageField


class SectionImageSerializer(BaseImageSerializer):
    class Meta:
        model = SectionImage
        fields = ['title', 'url', 'width', 'height', 'caption']


class SectionSerializer(serializers.ModelSerializer):
    """
    Serializer for section instance.
    """
    images = PublicFilteredImageField(serializer_class=SectionImageSerializer)
    type = serializers.SlugRelatedField(slug_field='identifier', read_only=True)
    type_name_singular = serializers.SlugRelatedField(source='type', slug_field='name_singular', read_only=True)
    type_name_plural = serializers.SlugRelatedField(source='type', slug_field='name_plural', read_only=True)
    commenting = EnumField(enum_type=Commenting)

    class Meta:
        model = Section
        fields = [
            'id', 'type', 'commenting', 'published',
            'title', 'abstract', 'content', 'created_at', 'created_by', 'images', 'n_comments',
            'plugin_identifier', 'plugin_data', 'type_name_singular', 'type_name_plural'
        ]


class SectionFieldSerializer(serializers.RelatedField):
    """
    Serializer for section field. A property of other instance.
    """

    def to_representation(self, section):
        return SectionSerializer(section, context=self.context).data


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


class RootSectionImageSerializer(SectionImageSerializer):
    """
    Serializer for root level SectionImage endpoint /v1/image/
    """
    hearing = serializers.CharField(source='section.hearing_id', read_only=True)

    class Meta(SectionImageSerializer.Meta):
        fields = SectionImageSerializer.Meta.fields + ['section', 'hearing']


class ImagePagination(LimitOffsetPagination):
    default_limit = 50


class ImageFilter(filters.FilterSet):
    hearing = django_filters.CharFilter(name='section__hearing__id')
    section_type = django_filters.CharFilter(name='section__type__identifier')

    class Meta:
        model = SectionImage
        fields = ['section', 'hearing', 'section_type']


# root level SectionImage endpoint
class ImageViewSet(AdminsSeeUnpublishedMixin, viewsets.ReadOnlyModelViewSet):
    model = SectionImage
    serializer_class = RootSectionImageSerializer
    pagination_class = ImagePagination
    filter_class = ImageFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        return filter_by_hearing_visible(queryset, self.request, 'section__hearing')


class RootSectionSerializer(SectionSerializer):
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


class SectionPagination(LimitOffsetPagination):
    default_limit = 50


# root level Section endpoint
class RootSectionViewSet(AdminsSeeUnpublishedMixin, viewsets.ReadOnlyModelViewSet):
    serializer_class = RootSectionSerializer
    model = Section
    pagination_class = SectionPagination
    filter_class = SectionFilter

    def get_queryset(self):
        queryset = super().get_queryset()
        queryset = filter_by_hearing_visible(queryset, self.request)

        n = now()
        open_hearings = Q(hearing__force_closed=False) & Q(hearing__open_at__lte=n) & Q(hearing__close_at__gt=n)
        queryset = queryset.exclude(open_hearings, type__identifier=InitialSectionType.CLOSURE_INFO)

        return queryset
