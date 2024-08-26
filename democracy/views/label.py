import django_filters
from rest_framework import mixins, permissions, response, serializers, status, viewsets

from audit_log.views import AuditLogApiView
from democracy.models import Label
from democracy.pagination import DefaultLimitPagination
from democracy.views.utils import TranslatableSerializer


class LabelFilterSet(django_filters.rest_framework.FilterSet):
    label = django_filters.CharFilter(lookup_expr="icontains", field_name="translations__label")

    class Meta:
        model = Label
        fields = ["label"]


class LabelSerializer(serializers.ModelSerializer, TranslatableSerializer):
    class Meta:
        model = Label
        fields = ("id", "label")


class LabelViewSet(AuditLogApiView, viewsets.ReadOnlyModelViewSet, mixins.CreateModelMixin):
    serializer_class = LabelSerializer
    queryset = Label.objects.all()
    pagination_class = DefaultLimitPagination
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filterset_class = LabelFilterSet

    def create(self, request):
        if not request.user or not request.user.get_default_organization():
            return response.Response(
                {"status": "User without organization cannot POST labels."}, status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request)
