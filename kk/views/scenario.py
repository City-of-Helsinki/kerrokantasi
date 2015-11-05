from rest_framework import serializers

from kk.models import Scenario

# Serializer for scenario


class ScenarioSerializer(serializers.ModelSerializer):

    class Meta:
        model = Scenario
        fields = ['abstract', 'content', 'created_at', 'created_by']

# Serializer for 'scenarios' field.


class ScenarioFieldSerializer(serializers.RelatedField):

    def to_representation(self, scenario):
        return {
            'abstract': scenario.abstract,
            'content': scenario.content,
            'created_at': scenario.created_at,
            'created_by': scenario.created_by
        }
