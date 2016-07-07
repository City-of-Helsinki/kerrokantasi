from django.contrib.auth import get_user_model
from rest_framework import permissions, serializers, viewsets


class ForeignKeyListSerializer(serializers.ReadOnlyField):

    def to_representation(self, value):
        return value.all().values_list('pk', flat=True)


class UserDataSerializer(serializers.ModelSerializer):
    voted_section_comments = ForeignKeyListSerializer(source='voted_democracy_sectioncomment')
    followed_hearings = ForeignKeyListSerializer()
    admin_organizations = serializers.SlugRelatedField('name', many=True, read_only=True)

    class Meta:
        model = get_user_model()
        fields = [
            'uuid',
            'username', 'first_name', 'last_name',
            'voted_section_comments', 'followed_hearings',
            'admin_organizations'
        ]


class UserDataViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = UserDataSerializer
    permission_classes = (permissions.IsAuthenticated,)
    lookup_field = 'uuid'

    def get_queryset(self, *args, **kwargs):
        return get_user_model().objects.filter(pk=self.request.user.pk)
