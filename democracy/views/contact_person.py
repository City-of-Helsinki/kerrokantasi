from rest_framework import mixins, permissions, serializers, viewsets

from democracy.models import ContactPerson, Organization
from democracy.pagination import DefaultLimitPagination
from democracy.views.utils import TranslatableSerializer


class ContactPersonPermission(permissions.BasePermission):
    message = "User without organization cannot access contact persons."

    def has_permission(self, request, view):
        return bool(hasattr(request.user, "get_default_organization") and request.user.get_default_organization())


class ContactPersonSerializer(serializers.ModelSerializer, TranslatableSerializer):
    organization = serializers.SlugRelatedField("name", queryset=Organization.objects.all(), allow_null=True)
    external_organization = serializers.BooleanField(source="organization.external_organization", read_only=True)

    class Meta:
        model = ContactPerson
        fields = ("id", "title", "name", "phone", "email", "organization", "external_organization", "additional_info")

    def create(self, validated_data):
        if not validated_data["organization"]:
            validated_data["organization"] = self.context["request"].user.get_default_organization()
        return super().create(validated_data)


class ContactPersonViewSet(viewsets.ReadOnlyModelViewSet, mixins.CreateModelMixin, mixins.UpdateModelMixin):
    serializer_class = ContactPersonSerializer
    queryset = ContactPerson.objects.select_related("organization").order_by("name")
    permission_classes = [permissions.IsAuthenticated, ContactPersonPermission]
    pagination_class = DefaultLimitPagination
