from drf_spectacular.utils import (
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import mixins, permissions, serializers, viewsets

from audit_log.views import AuditLogApiView
from democracy.models import ContactPerson, Organization
from democracy.pagination import DefaultLimitPagination
from democracy.views.openapi import PAGINATION_PARAMS
from democracy.views.utils import TranslatableSerializer


class ContactPersonPermission(permissions.BasePermission):
    message = "User without organization cannot access contact persons."

    def has_permission(self, request, view):
        return bool(
            hasattr(request.user, "get_default_organization")
            and request.user.get_default_organization()
        )


class ContactPersonSerializer(serializers.ModelSerializer, TranslatableSerializer):
    organization = serializers.SlugRelatedField(
        "name", queryset=Organization.objects.all(), allow_null=True
    )
    external_organization = serializers.BooleanField(
        source="organization.external_organization", read_only=True
    )

    class Meta:
        model = ContactPerson
        fields = (
            "id",
            "title",
            "name",
            "phone",
            "email",
            "organization",
            "external_organization",
            "additional_info",
        )

    def create(self, validated_data):
        if not validated_data["organization"]:
            validated_data["organization"] = self.context[
                "request"
            ].user.get_default_organization()
        return super().create(validated_data)


@extend_schema_view(
    list=extend_schema(
        summary="List contact persons",
        description=(
            "Retrieve paginated list of contact persons. "
            "Requires authentication and user must belong to an organization."
        ),
        parameters=PAGINATION_PARAMS,
    ),
    retrieve=extend_schema(
        summary="Get contact person details",
        description=(
            "Retrieve detailed information about a specific contact person. "
            "Requires authentication and user must belong to an organization."
        ),
    ),
    create=extend_schema(
        summary="Create contact person",
        description=(
            "Create a new contact person for the user's organization. "
            "If organization is not specified, user's default organization is used."
        ),
        responses={
            201: ContactPersonSerializer,
            403: OpenApiResponse(
                description="User without organization cannot create contact persons"
            ),
        },
    ),
    update=extend_schema(
        summary="Update contact person",
        description=(
            "Update an existing contact person. "
            "Requires authentication and user must belong to an organization."
        ),
        responses={
            200: ContactPersonSerializer,
            403: OpenApiResponse(
                description="User without organization cannot update contact persons"
            ),
        },
    ),
    partial_update=extend_schema(
        summary="Partially update contact person",
        description=(
            "Partially update an existing contact person. "
            "Requires authentication and user must belong to "
            "an organization."
        ),
        responses={
            200: ContactPersonSerializer,
            403: OpenApiResponse(
                description="User without organization cannot update contact persons"
            ),
        },
    ),
)
class ContactPersonViewSet(
    AuditLogApiView,
    viewsets.ReadOnlyModelViewSet,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
):
    """
    API endpoint for contact persons.

    Manages contact persons associated with organizations. Contact persons are used
    in hearings to provide points of contact for the public.
    """

    serializer_class = ContactPersonSerializer
    queryset = ContactPerson.objects.select_related("organization").order_by("name")
    permission_classes = [permissions.IsAuthenticated, ContactPersonPermission]
    pagination_class = DefaultLimitPagination
