from rest_framework import serializers, viewsets

from democracy.models import ContactPerson
from democracy.pagination import DefaultLimitPagination


class ContactPersonSerializer(serializers.ModelSerializer):
    organization = serializers.SlugRelatedField('name', read_only=True)

    class Meta:
        model = ContactPerson
        fields = ('id', 'title', 'name', 'phone', 'email', 'organization')


class ContactPersonViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ContactPersonSerializer
    queryset = ContactPerson.objects.select_related('organization')
    pagination_class = DefaultLimitPagination
