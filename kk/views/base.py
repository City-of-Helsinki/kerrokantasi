from kk.models.images import BaseImage
from kk.views.utils import AbstractSerializerMixin
from rest_framework import serializers


class UserFieldSerializer(serializers.ModelSerializer):
    def to_representation(self, user):
        return user.username


class CreatedBySerializer(serializers.ModelSerializer):
    created_by = UserFieldSerializer()


class BaseImageSerializer(AbstractSerializerMixin, serializers.ModelSerializer):
    """
    Serializer for Image objects.
    """
    url = serializers.SerializerMethodField()

    class Meta:
        model = BaseImage
        fields = ['title', 'url', 'width', 'height', 'caption']

    def get_url(self, obj):
        url = obj.image.url
        if not self.context:
            raise NotImplementedError("Not implemented")  # pragma: no cover

        request = self.context.get("request")
        if request:
            url = request.build_absolute_uri(url)

        return url
