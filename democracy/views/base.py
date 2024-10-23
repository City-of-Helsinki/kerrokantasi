from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from rest_framework import serializers

from democracy.models.base import BaseModel
from democracy.models.files import BaseFile
from democracy.models.images import BaseImage


class UserFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()

    def to_representation(self, user):
        return {
            "uuid": user.uuid,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }


class CreatedBySerializer(serializers.ModelSerializer):
    created_by = UserFieldSerializer()


class BaseImageSerializer(serializers.ModelSerializer):
    """
    Serializer for Image objects.
    """

    url = serializers.SerializerMethodField()

    class Meta:
        model = BaseImage
        fields = ["title", "url", "width", "height", "caption"]

    def get_url(self, obj):
        url = self._get_image(obj).url
        request = self._get_context_request()
        if request:  # pragma: no branch
            url = request.build_absolute_uri(url)
        return url

    def _get_image(self, obj):
        return obj.image

    def _get_context_request(self):
        if not self.context:
            raise NotImplementedError("Not implemented")  # pragma: no cover
        return self.context.get("request")


class BaseFileSerializer(serializers.ModelSerializer):
    """
    Serializer for File objects.
    """

    url = serializers.SerializerMethodField()
    filetype = None

    class Meta:
        model = BaseFile
        fields = ["title", "url", "caption"]

    def get_url(self, obj):
        if not obj.pk:
            return None
        url = reverse("serve_file", kwargs={"filetype": self.filetype, "pk": obj.pk})
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
                "AdminsSeeUnpublishedMixin requires `model` to be a BaseModel subclass (it's %r)"  # noqa: E501
                % self.model
            )
        user = self._get_user_from_request_or_context()

        if user is None:  # pragma: no cover
            raise ImproperlyConfigured(
                "%r has no request or serialization context; AdminsSeeUnpublishedMixin requires one"  # noqa: E501
                % self
            )

        if user.is_authenticated and user.is_superuser:
            return self.model.objects.with_unpublished()
        else:
            return self.model.objects.public()

    def _get_user_from_request_or_context(self):
        if hasattr(self, "request"):  # pragma: no branch
            return getattr(self.request, "user", None)
