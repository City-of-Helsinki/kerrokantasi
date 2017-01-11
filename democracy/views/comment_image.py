from democracy.models.section import CommentImage
from democracy.views.base import BaseImageSerializer
from democracy.views.utils import Base64ImageField


class CommentImageSerializer(BaseImageSerializer):
    class Meta:
        model = CommentImage
        fields = ['url', 'width', 'height', 'title', 'caption', 'id']


class CommentImageCreateSerializer(BaseImageSerializer):
    """
    Serializer for comment_image creation.
    """
    image = Base64ImageField()

    class Meta:
        model = CommentImage
        fields = ['title', 'image', 'id', 'width', 'height', 'caption']
