from rest_framework import serializers

from kk.models import HearingImage

# Serializer for image


class ImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = HearingImage
        fields = ['title', 'image', 'width', 'height']

# Serializer for 'image' field.


class ImageFieldSerializer(serializers.RelatedField):

    def to_representation(self, image):
        return {'name': image.title, 'url': image.image.url, 'type': image.type,
                'width': image.width, 'height': image.height}
