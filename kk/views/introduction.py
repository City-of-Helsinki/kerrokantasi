from rest_framework import serializers

from kk.models import Introduction
from .image import ImageFieldSerializer


# Serializer for introduction


class IntroductionSerializer(serializers.ModelSerializer):

    images = ImageFieldSerializer(many=True, read_only=True)

    class Meta:
        model = Introduction
        fields = ['abstract', 'content', 'created_at', 'created_by', 'images']

# Serializer for 'introductions' field.


class IntroductionFieldSerializer(serializers.RelatedField):

    def to_representation(self, intro):
        return IntroductionSerializer(intro, context=self.context).data
