from kk.models.scenario import ScenarioImage
from kk.views.base import BaseImageSerializer
from rest_framework import serializers
from kk.models import Scenario


class ScenarioImageSerializer(BaseImageSerializer):
    class Meta:
        model = ScenarioImage
        fields = ['title', 'url', 'width', 'height', 'caption']


class ScenarioSerializer(serializers.ModelSerializer):
    images = ScenarioImageSerializer.get_field_serializer(many=True, read_only=True)

    class Meta:
        model = Scenario
        fields = ['title', 'abstract', 'content', 'created_at', 'created_by', 'images']


# Serializer for 'scenarios' field.


class ScenarioFieldSerializer(serializers.RelatedField):
    def to_representation(self, scenario):
        return ScenarioSerializer(scenario, context=self.context).data
