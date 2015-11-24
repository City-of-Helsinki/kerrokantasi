from kk.models import HearingComment
from kk.views.comment import BaseCommentSerializer, BaseCommentViewSet


class HearingCommentSerializer(BaseCommentSerializer):

    class Meta:
        model = HearingComment
        fields = ['id', 'hearing', 'content', 'n_votes', 'created_by', 'created_at']


class HearingCommentCreateSerializer(BaseCommentSerializer):

    class Meta:
        model = HearingComment
        fields = ['content', 'hearing']


class HearingCommentViewSet(BaseCommentViewSet):
    model = HearingComment
    serializer_class = HearingCommentSerializer
    create_serializer_class = HearingCommentCreateSerializer
