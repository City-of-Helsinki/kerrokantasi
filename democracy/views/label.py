from rest_framework import serializers, viewsets, filters
import django_filters

from democracy.models import Label
from democracy.pagination import DefaultLimitPagination


class LabelFilter(django_filters.FilterSet):
    label = django_filters.CharFilter(lookup_type='icontains')

    class Meta:
        model = Label
        fields = ['label']


class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ('id', 'label')


class LabelViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LabelSerializer
    queryset = Label.objects.all()
    pagination_class = DefaultLimitPagination
    filter_backends = (filters.DjangoFilterBackend,)
    filter_class = LabelFilter
