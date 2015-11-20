from kk.models import SectionComment
from kk.views.comment import BaseCommentViewSet
from rest_framework import serializers

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
        fields = ['id', 'section', 'content', 'n_votes', 'created_by', 'created_at']


class SectionCommentViewSet(BaseCommentViewSet):
    queryset = SectionComment.objects.all()
    serializer_class = SectionCommentSerializer
    create_serializer_class = SectionCommentCreateSerializer
