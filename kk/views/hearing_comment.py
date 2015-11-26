from kk.models import HearingComment
from kk.views.comment import BaseCommentSerializer, BaseCommentViewSet, COMMENT_FIELDS


class HearingCommentSerializer(BaseCommentSerializer):

    class Meta:
        model = HearingComment
        fields = ['hearing'] + COMMENT_FIELDS


class HearingCommentCreateSerializer(BaseCommentSerializer):

    class Meta:
        model = HearingComment
        fields = ['content', 'hearing']


class HearingCommentViewSet(BaseCommentViewSet):
    model = HearingComment
    serializer_class = HearingCommentSerializer
    create_serializer_class = HearingCommentCreateSerializer
