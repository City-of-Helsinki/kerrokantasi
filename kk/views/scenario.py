from kk.models.scenario import ScenarioImage
from kk.views.base import BaseImageSerializer
from rest_framework import serializers
from rest_framework import viewsets

from kk.models import Scenario


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
