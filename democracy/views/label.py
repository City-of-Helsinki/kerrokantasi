from rest_framework import serializers, viewsets

from democracy.models import Label
from democracy.pagination import DefaultLimitPagination


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ('id', 'label')


class LabelViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LabelSerializer
    queryset = Label.objects.all()
    pagination_class = DefaultLimitPagination
