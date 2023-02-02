from rest_framework import mixins, permissions, response, serializers, status, viewsets

from democracy.models import ContactPerson, Organization
from democracy.pagination import DefaultLimitPagination
from democracy.views.utils import TranslatableSerializer


class ContactPersonSerializer(serializers.ModelSerializer, TranslatableSerializer):
    organization = serializers.SlugRelatedField("name", queryset=Organization.objects.all(), allow_null=True)
    external_organization = serializers.BooleanField(source="organization.external_organization", read_only=True)

    class Meta:
        model = ContactPerson
        fields = ("id", "title", "name", "phone", "email", "organization", "external_organization", "additional_info")

    def create(self, validated_data):
        if not validated_data["organization"]:
            validated_data["organization"] = self.context['request'].user.get_default_organization()
        return super().create(validated_data)


class ContactPersonViewSet(viewsets.ReadOnlyModelViewSet, mixins.CreateModelMixin, mixins.UpdateModelMixin):
    serializer_class = ContactPersonSerializer
    queryset = ContactPerson.objects.select_related("organization").order_by("name")
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = DefaultLimitPagination

    def create(self, request, **kwargs):
        if not request.user or not request.user.get_default_organization():
            return response.Response(
                {'status': 'User without organization cannot POST contact persons.'}, status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request, **kwargs)

    def update(self, request, pk=None, partial=False):
        if not request.user or not request.user.get_default_organization():
            return response.Response(
                {'status': 'User without organization cannot PUT contact persons.'}, status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, pk=pk, partial=partial)
