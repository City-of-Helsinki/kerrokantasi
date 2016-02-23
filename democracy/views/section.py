from rest_framework import serializers, viewsets

from democracy.enums import Commenting, SectionType
from democracy.models import Section, SectionImage, Hearing
from democracy.utils.drf_enum_field import EnumField
from democracy.views.base import AdminsSeeUnpublishedMixin, BaseImageSerializer


class SectionImageSerializer(BaseImageSerializer):

    class Meta:
        model = SectionImage
        fields = ['title', 'url', 'width', 'height', 'caption']


class SectionSerializer(serializers.ModelSerializer):
    """
    Serializer for section instance.
    """
    images = SectionImageSerializer.get_field_serializer(many=True, read_only=True)
    type = EnumField(enum_type=SectionType)
    commenting = EnumField(enum_type=Commenting)

    class Meta:
        model = Section
        fields = [
            'id', 'type', 'commenting', 'published',
            'title', 'abstract', 'content', 'created_at', 'created_by', 'images', 'n_comments',
            'plugin_identifier', 'plugin_data',
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
        hearing = Hearing.objects.get(id=self.kwargs['hearing_pk'])
        queryset = super().get_queryset().filter(hearing=hearing)
        if not hearing.closed:
            queryset = queryset.exclude(type=SectionType.CLOSURE_INFO)
        return queryset
