from rest_framework import serializers

from kk.models import Image

# Serializer for image


class ImageSerializer(serializers.ModelSerializer):

    class Meta:
        model = Image
        fields = ['title', 'image', 'width', 'height', 'caption']

# Serializer for 'image' field.


class ImageFieldSerializer(serializers.RelatedField):
    """
    Serializer for nested image fields.
    """

    def to_representation(self, image):
        return ImageSerializer(image, context=self.context).data
