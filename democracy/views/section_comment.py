from rest_framework import serializers

from democracy.models import SectionComment
from democracy.views.comment import COMMENT_FIELDS, BaseCommentViewSet

from .base import CreatedBySerializer


class SectionCommentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for comments creation.
    """

    class Meta:
        model = SectionComment
        fields = ['section', 'content']


class SectionCommentSerializer(CreatedBySerializer, serializers.ModelSerializer):
    """
    Serializer for comment added to section.
    """

    class Meta:
        model = SectionComment
        fields = ['section'] + COMMENT_FIELDS


class SectionCommentViewSet(BaseCommentViewSet):
    model = SectionComment
    serializer_class = SectionCommentSerializer
    create_serializer_class = SectionCommentCreateSerializer
