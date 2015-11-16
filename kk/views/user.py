from django.contrib.auth import get_user_model
from rest_framework import permissions, serializers, viewsets


class ForeignKeyListSerializer(serializers.ReadOnlyField):
    def to_representation(self, value):
        return value.all().values_list('pk', flat=True)


class UserDataSerializer(serializers.ModelSerializer):
    voted_hearing_comments = ForeignKeyListSerializer(source='voted_kk_hearingcomment')
    voted_scenario_comments = ForeignKeyListSerializer(source='voted_kk_scenariocomment')
    followed_hearings = ForeignKeyListSerializer()

    class Meta:
        model = get_user_model()
        fields = ['uuid', 'username', 'voted_hearing_comments', 'voted_scenario_comments', 'followed_hearings']


class UserDataView(viewsets.generics.RetrieveAPIView):
    model = get_user_model()
    serializer_class = UserDataSerializer
    permission_classes = (permissions.IsAuthenticated, )

    def get_object(self, *args, **kwargs):
        return self.request.user