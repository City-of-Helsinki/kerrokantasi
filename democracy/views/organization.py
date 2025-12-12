from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import mixins, permissions, serializers
from rest_framework.viewsets import GenericViewSet

from democracy.models import Organization
from democracy.pagination import DefaultLimitPagination


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("name", "external_organization")


@extend_schema_view(
    list=extend_schema(
        summary="List organizations",
        description="Retrieve paginated list of all organizations in the system.",
        parameters=[
            OpenApiParameter(
                "limit", OpenApiTypes.INT, description="Number of results per page"
            ),
            OpenApiParameter(
                "offset", OpenApiTypes.INT, description="Offset for pagination"
            ),
        ],
    ),
)
class OrganizationViewSet(mixins.ListModelMixin, GenericViewSet):
    """
    API endpoint for organizations.

    Organizations are entities that create and manage hearings. Read-only endpoint
    for listing available organizations.
    """

    serializer_class = OrganizationSerializer
    queryset = Organization.objects.all()
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = DefaultLimitPagination
