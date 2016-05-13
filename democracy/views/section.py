from rest_framework import serializers, viewsets

from democracy.enums import Commenting, InitialSectionType
from democracy.models import Hearing, Section, SectionImage
from democracy.utils.drf_enum_field import EnumField
from democracy.views.base import AdminsSeeUnpublishedMixin, BaseImageSerializer
from democracy.views.utils import PublicFilteredImageField


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
