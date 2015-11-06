from rest_framework import serializers
from kk.models import Image


class ImageSerializer(serializers.ModelSerializer):
    """
    Serializer for Image objects.
    """
    url = serializers.SerializerMethodField()

    class Meta:
        model = Image
        fields = ['title', 'url', 'width', 'height', 'caption']

    def get_url(self, obj):
        url = obj.image.url
        if not self.context:
            raise NotImplementedError("Not implemented")

        request = self.context.get("request")
        if request:
            url = request.build_absolute_uri(url)

        return url


class ImageFieldSerializer(serializers.RelatedField):
    """
    Serializer for nested image fields.
    """

    def to_representation(self, image):
        return ImageSerializer(image, context=self.context).data
