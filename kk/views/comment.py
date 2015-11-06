from rest_framework import serializers

from kk.models import Comment
from .base import CreatedBySerializer


# Serializer for comment


class CommentSerializer(CreatedBySerializer, serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = ['content', 'votes', 'created_by', 'created_at']


# Serializer to create comment


class CommentCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = Comment
        fields = ['content']


# Serializer for 'comments' field.


class CommentFieldSerializer(serializers.RelatedField):

    def to_representation(self, comment):
        return CommentSerializer(comment).data
