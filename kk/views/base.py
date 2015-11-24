from django.core.exceptions import ImproperlyConfigured
from kk.models.base import BaseModel
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


class AdminsSeeUnpublishedMixin(object):
    model = None

    def get_queryset(self):
        if not (self.model and issubclass(self.model, BaseModel)):  # pragma: no cover
            raise ImproperlyConfigured(
                "AdminsSeeUnpublishedMixin requires `model` to be a BaseModel subclass (it's %r)" % self.model
            )
        user = self._get_user_from_request_or_context()

        if user is None:  # pragma: no cover
            raise ImproperlyConfigured(
                "%r has no request or serialization context; AdminsSeeUnpublishedMixin requires one" % self
            )

        if user.is_authenticated() and user.is_superuser:
            return self.model.objects.with_unpublished()
        else:
            return self.model.objects.all()

    def _get_user_from_request_or_context(self):
        if hasattr(self, "request"):  # pragma: no branch
            return getattr(self.request, "user", None)
