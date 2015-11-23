from rest_framework import serializers

from kk.models.images import BaseImage
from kk.views.utils import AbstractSerializerMixin


class UserFieldSerializer(serializers.ModelSerializer):

    def to_representation(self, user):
        return {
            "uuid": user.uuid,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }


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
        if request:  # pragma: no branch
            url = request.build_absolute_uri(url)

        return url
