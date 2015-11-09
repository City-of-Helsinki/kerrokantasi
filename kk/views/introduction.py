from kk.views.base import BaseImageSerializer
from rest_framework import serializers
from kk.models import Introduction, IntroductionImage


class IntroductionImageSerializer(BaseImageSerializer):
    class Meta:
        model = IntroductionImage
        fields = ['title', 'url', 'width', 'height', 'caption']


class IntroductionSerializer(serializers.ModelSerializer):
    images = IntroductionImageSerializer.get_field_serializer(many=True, read_only=True)

    class Meta:
        model = Introduction
        fields = ['abstract', 'content', 'created_at', 'created_by', 'images']


# Serializer for 'introductions' field.


class IntroductionFieldSerializer(serializers.RelatedField):
    def to_representation(self, intro):
        return IntroductionSerializer(intro, context=self.context).data
