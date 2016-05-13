from django.db.models import Q
from rest_framework.exceptions import ValidationError

from democracy.models import Hearing, HearingComment
from democracy.views.comment import COMMENT_FIELDS, BaseCommentSerializer, BaseCommentViewSet


class HearingCommentSerializer(BaseCommentSerializer):
    class Meta:
        model = HearingComment
        fields = ['hearing'] + COMMENT_FIELDS


class HearingCommentCreateSerializer(BaseCommentSerializer):
    class Meta:
        model = HearingComment
        fields = ['content', 'hearing', 'authorization_code']

    def validate(self, attrs):
        attrs = super().validate(attrs)

        if not attrs.get("content"):
            raise ValidationError("Content must be supplied.")

        return attrs


class HearingCommentViewSet(BaseCommentViewSet):
    model = HearingComment
    serializer_class = HearingCommentSerializer
    create_serializer_class = HearingCommentCreateSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()

        id_or_slug = self.get_comment_parent_id()
        obj = Hearing.objects.get_by_id_or_slug(id_or_slug)
        context["comment_parent"] = obj.id
        return context

    def get_comment_parent(self):
        id_or_slug = self.get_comment_parent_id()
        return Hearing.objects.get_by_id_or_slug(id_or_slug)

    def get_queryset(self):
        queryset = super(BaseCommentViewSet, self).get_queryset()
        id_or_slug = self.get_comment_parent_id()

        return queryset.filter(Q(hearing=id_or_slug) | Q(hearing__slug=id_or_slug))
