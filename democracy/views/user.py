from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework import permissions, serializers, viewsets

from democracy.models import SectionPollAnswer


class ForeignKeyListSerializer(serializers.ReadOnlyField):
    def to_representation(self, value):
        return value.all().values_list("pk", flat=True)


class UserDataSerializer(serializers.ModelSerializer):
    voted_section_comments = ForeignKeyListSerializer(
        source="voted_democracy_sectioncomment"
    )
    answered_questions = serializers.SerializerMethodField(read_only=True)
    followed_hearings = ForeignKeyListSerializer()
    admin_organizations = serializers.SlugRelatedField(
        "name", many=True, read_only=True
    )

    class Meta:
        model = get_user_model()
        fields = [
            "uuid",
            "username",
            "first_name",
            "last_name",
            "nickname",
            "voted_section_comments",
            "followed_hearings",
            "admin_organizations",
            "answered_questions",
            "has_strong_auth",
        ]

    def get_answered_questions(self, obj):
        return SectionPollAnswer.objects.filter(comment__created_by=obj).values_list(
            "option__poll_id", flat=True
        )


@extend_schema_view(
    list=extend_schema(
        summary="Get current user data",
        description=(
            "Retrieve data for the currently authenticated user. "
            "Returns only the authenticated user's own data."
        ),
    ),
    retrieve=extend_schema(
        summary="Get user data by UUID",
        description=(
            "Retrieve user data by UUID. Users can only access their own data."
        ),
    ),
)
class UserDataViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for user data.

    Provides access to current user's profile data including voting history,
    followed hearings, and organization memberships. Users can only access
    their own data.
    """

    serializer_class = UserDataSerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_field = "uuid"

    def get_queryset(self, *args, **kwargs):
        return get_user_model().objects.filter(pk=self.request.user.pk)
