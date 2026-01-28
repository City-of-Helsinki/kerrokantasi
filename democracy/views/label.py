import django_filters
from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import mixins, permissions, response, serializers, status, viewsets

from audit_log.views import AuditLogApiView
from democracy.models import Label
from democracy.pagination import DefaultLimitPagination
from democracy.views.openapi import LABEL_FILTER_PARAMS, PAGINATION_PARAMS
from democracy.views.utils import TranslatableSerializer


class LabelFilterSet(django_filters.rest_framework.FilterSet):
    label = django_filters.CharFilter(
        lookup_expr="icontains",
        field_name="translations__label",
        help_text="Filter by label text (case-insensitive contains)",
    )

    class Meta:
        model = Label
        fields = ["label"]


class LabelSerializer(serializers.ModelSerializer, TranslatableSerializer):
    class Meta:
        model = Label
        fields = ("id", "label")


@extend_schema_view(
    list=extend_schema(
        summary="List labels",
        description="Retrieve paginated list of labels used for categorizing hearings.",
        parameters=PAGINATION_PARAMS + LABEL_FILTER_PARAMS,
    ),
    retrieve=extend_schema(
        summary="Get label details",
        description="Retrieve detailed information about a specific label.",
    ),
    create=extend_schema(
        summary="Create label",
        description=(
            "Create a new label. "
            "Requires authentication and user must belong to an organization."
        ),
        responses={
            201: LabelSerializer,
            403: OpenApiResponse(
                description="User without organization cannot create labels"
            ),
        },
    ),
)
class LabelViewSet(
    AuditLogApiView, viewsets.ReadOnlyModelViewSet, mixins.CreateModelMixin
):
    """
    API endpoint for labels.

    Labels are used to categorize and tag hearings for easier filtering and
    organization.
    """

    serializer_class = LabelSerializer
    queryset = Label.objects.all().prefetch_related("translations")
    pagination_class = DefaultLimitPagination
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filterset_class = LabelFilterSet

    def create(self, request):
        if not request.user or not request.user.get_default_organization():
            return response.Response(
                {"status": "User without organization cannot POST labels."},
                status=status.HTTP_403_FORBIDDEN,
            )
        return super().create(request)
