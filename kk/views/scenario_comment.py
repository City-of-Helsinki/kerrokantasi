from kk.models import ScenarioComment

from kk.views.comment import BaseCommentViewSet
from rest_framework import serializers
from .base import CreatedBySerializer


class ScenarioCommentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for comments creation.
    """

    class Meta:
        model = ScenarioComment
        fields = ['content', 'scenario']


class ScenarioCommentSerializer(CreatedBySerializer, serializers.ModelSerializer):
    """
    Serializer for comment added to scenario.
    """

    class Meta:
        model = ScenarioComment
        fields = ['content', 'scenario', 'votes', 'created_by', 'created_at']


class ScenarioCommentViewSet(BaseCommentViewSet):
    queryset = ScenarioComment.objects.all()
    serializer_class = ScenarioCommentSerializer
    create_serializer_class = ScenarioCommentCreateSerializer
