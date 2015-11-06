from rest_framework import serializers

from kk.models import Scenario
from .image import ImageFieldSerializer


# Serializer for scenario


class ScenarioSerializer(serializers.ModelSerializer):

    images = ImageFieldSerializer(many=True, read_only=True)

    class Meta:
        model = Scenario
        fields = ['title', 'abstract', 'content', 'created_at', 'created_by', 'images']

# Serializer for 'scenarios' field.


class ScenarioFieldSerializer(serializers.RelatedField):

    def to_representation(self, scenario):
        return ScenarioSerializer(scenario).data
