from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.serializers import get_validation_error_detail
from rest_framework.settings import api_settings

from democracy.models import SectionComment
from democracy.models.section import Section
from democracy.views.comment import COMMENT_FIELDS, BaseCommentViewSet

from .base import CreatedBySerializer


class SectionCommentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for comments creation.
    """

    class Meta:
        model = SectionComment
        fields = ['section', 'content', 'plugin_data']

    def to_internal_value(self, data):
        if data.get("plugin_data") is None:
            data["plugin_data"] = ""
        return super(SectionCommentCreateSerializer, self).to_internal_value(data)

    def validate(self, attrs):
        if attrs.get("plugin_data"):
            section = Section.objects.get(pk=self.context["comment_parent"])
            try:
                if not section.plugin_identifier:
                    raise ValidationError("The section %s has no plugin; no plugin data is allowed." % section)
                plugin = section.plugin_implementation
                attrs["plugin_data"] = plugin.clean_client_data(attrs["plugin_data"])
            except (ValidationError, DjangoValidationError) as ve:
                # Massage the validation error slightly...
                detail = get_validation_error_detail(ve)
                detail.setdefault("plugin_data", []).extend(detail.pop(api_settings.NON_FIELD_ERRORS_KEY, ()))
                raise ValidationError(detail=detail)
            attrs["plugin_identifier"] = section.plugin_identifier
        return attrs


class SectionCommentSerializer(CreatedBySerializer, serializers.ModelSerializer):
    """
    Serializer for comment added to section.
    """

    class Meta:
        model = SectionComment
        fields = ['section'] + COMMENT_FIELDS


class SectionCommentViewSet(BaseCommentViewSet):
    model = SectionComment
    serializer_class = SectionCommentSerializer
    create_serializer_class = SectionCommentCreateSerializer
