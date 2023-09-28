from rest_framework import mixins, permissions, serializers
from rest_framework.viewsets import GenericViewSet

from democracy.models import Organization
from democracy.pagination import DefaultLimitPagination


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ("name", "external_organization")


class OrganizationViewSet(mixins.ListModelMixin, GenericViewSet):
    serializer_class = OrganizationSerializer
    queryset = Organization.objects.all()
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = DefaultLimitPagination
