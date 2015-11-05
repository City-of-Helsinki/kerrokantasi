from rest_framework import serializers

from kk.models import Introduction

# Serializer for introduction
class IntroductionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Introduction
        fields = ['abstract', 'content', 'created_at', 'created_by']

# Serializer for 'introductions' field.
class IntroductionFieldSerializer(serializers.RelatedField):

    def to_representation(self, intro):
        return {
            'abstract': intro.abstract,
            'content': intro.content,
            'created_at': intro.created_at,
            'created_by': intro.created_by
        }
