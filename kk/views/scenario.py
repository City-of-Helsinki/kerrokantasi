from django.shortcuts import get_object_or_404

from kk.models import Scenario
from kk.models.scenario import ScenarioImage
from kk.views.base import BaseImageSerializer
from rest_framework import serializers, viewsets
from rest_framework.response import Response


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
        fields = ['id', 'title', 'abstract', 'content', 'created_at', 'created_by', 'images', 'n_comments']


class ScenarioFieldSerializer(serializers.RelatedField):
    """
    Serializer for scenario field. A property of other instance.
    """

    def to_representation(self, scenario):
        return ScenarioSerializer(scenario, context=self.context).data


class ScenarioViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ScenarioSerializer

    def get_queryset(self):
        return Scenario.objects.filter(hearing_id=self.kwargs["hearing_pk"])
