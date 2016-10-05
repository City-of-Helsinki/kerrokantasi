from rest_framework import serializers, viewsets

from democracy.models import Label
from democracy.pagination import DefaultLimitPagination


class LabelFieldSerializer(serializers.RelatedField):
    # Serializer for labels. Get label names instead of IDs.

    def to_representation(self, value):
        return value.label


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ('id', 'label')


class LabelViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LabelSerializer
    queryset = Label.objects.all()
    pagination_class = DefaultLimitPagination
