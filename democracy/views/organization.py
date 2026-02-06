from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import mixins, permissions, serializers
from rest_framework.viewsets import GenericViewSet

from democracy.models import Organization
from democracy.pagination import DefaultLimitPagination
from democracy.views.openapi import PAGINATION_PARAMS


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("name", "external_organization")


@extend_schema_view(
    list=extend_schema(
        summary="List organizations",
        description="Retrieve paginated list of all organizations in the system.",
        parameters=PAGINATION_PARAMS,
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
