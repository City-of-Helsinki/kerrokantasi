from kk.models.scenario import ScenarioImage
from kk.views.base import BaseImageSerializer
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework import permissions
from rest_framework import status
from rest_framework.response import Response

from kk.models import Scenario, ScenarioComment
from .base import CreatedBySerializer


class ScenarioImageSerializer(BaseImageSerializer):

    class Meta:
        model = ScenarioImage
        fields = ['title', 'url', 'width', 'height', 'caption']


class ScenarioSerializer(serializers.ModelSerializer):
    """
    Serializer for scenario instance.
    """
    images = ScenarioImageSerializer.get_field_serializer(many=True, read_only=True)

    class Meta:
        model = Scenario
        fields = ['title', 'abstract', 'content', 'created_at', 'created_by', 'images']


class ScenarioFieldSerializer(serializers.RelatedField):
    """
    Serializer for scenario field. A property of other instance.
    """

    def to_representation(self, scenario):
        return ScenarioSerializer(scenario, context=self.context).data


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
        fields = ['content', 'votes', 'created_by', 'created_at']


class ScenarioViewSet(viewsets.ViewSet):
    serializer_class = ScenarioSerializer

    def list(self, request, hearing=None):
        queryset = Scenario.objects.filter(hearing=hearing)
        serializer = ScenarioSerializer(queryset, many=True)
        return Response(serializer.data)

    def retrieve(self, request, pk=None, hearing=None):
        queryset = Scenario.objects.filter(pk=pk, hearing=hearing)
        scenario = get_object_or_404(queryset, pk=pk)
        serializer = ScenarioSerializer(scenario)
        return Response(serializer.data)


class ScenarioCommentViewSet(viewsets.ModelViewSet):
    """
    Viewset for comments added to scenario.
    """
    queryset = ScenarioComment.objects.all()
    serializer_class = ScenarioCommentSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def create(self, request, *args, **kwargs):
        serializer = ScenarioCommentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
