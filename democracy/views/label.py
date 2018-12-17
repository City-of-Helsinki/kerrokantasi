from rest_framework import permissions
from rest_framework import response
from rest_framework import serializers, viewsets, mixins
import django_filters
from rest_framework import status

from democracy.models import Label
from democracy.pagination import DefaultLimitPagination
from democracy.views.utils import TranslatableSerializer


class LabelFilter(django_filters.rest_framework.FilterSet):
    label = django_filters.CharFilter(lookup_expr='icontains', name='translations__label')

    class Meta:
        model = Label
        fields = ['label']


class LabelSerializer(serializers.ModelSerializer, TranslatableSerializer):
    class Meta:
        model = Label
        fields = ('id', 'label')


class LabelViewSet(viewsets.ReadOnlyModelViewSet, mixins.CreateModelMixin):
    serializer_class = LabelSerializer
    queryset = Label.objects.all()
    pagination_class = DefaultLimitPagination
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filter_class = LabelFilter

    def create(self, request):
        if not request.user or not request.user.get_default_organization():
            return response.Response({'status': 'User without organization cannot POST labels.'},
                                     status=status.HTTP_403_FORBIDDEN)
        return super().create(request)
