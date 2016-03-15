from democracy.models import HearingComment
from democracy.views.comment import COMMENT_FIELDS, BaseCommentSerializer, BaseCommentViewSet


class HearingCommentSerializer(BaseCommentSerializer):

    class Meta:
        model = HearingComment
        fields = ['hearing'] + COMMENT_FIELDS


class HearingCommentCreateSerializer(BaseCommentSerializer):

    class Meta:
        model = HearingComment
        fields = ['content', 'hearing', 'authorization_code']


class HearingCommentViewSet(BaseCommentViewSet):
    model = HearingComment
    serializer_class = HearingCommentSerializer
    create_serializer_class = HearingCommentCreateSerializer
