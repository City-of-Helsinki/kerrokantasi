from democracy.models.section import CommentImage
from democracy.views.base import BaseImageSerializer


class CommentImageSerializer(BaseImageSerializer):
    class Meta:
        model = CommentImage
        fields = ["url", "width", "height", "title", "caption", "id"]
