from rest_framework import serializers, viewsets, permissions, mixins, response, status

from democracy.models import ContactPerson
from democracy.pagination import DefaultLimitPagination
from democracy.views.utils import TranslatableSerializer


class ContactPersonSerializer(serializers.ModelSerializer, TranslatableSerializer):
    organization = serializers.SlugRelatedField('name', read_only=True)

    class Meta:
        model = ContactPerson
        fields = ('id', 'title', 'name', 'phone', 'email', 'organization')

    def to_internal_value(self, value):
        if 'organization' in value:
            if value['organization'] not in map(str, self.context['request'].user.admin_organizations.all()):
                raise serializers.ValidationError(
                    {'organization': ("Setting organization to %(given)s " +
                                      "is not allowed for your organization. The organization" +
                                      " must be left blank or set to %(required)s.") %
                        {'given': value['organization'],
                         'required': self.context['request'].user.get_default_organization()}})
        return super().to_internal_value(value)

    def create(self, validated_data):
        # Always use the organization of the user
        validated_data['organization'] = self.context['request'].user.get_default_organization()
        return super().create(validated_data)


class ContactPersonViewSet(viewsets.ReadOnlyModelViewSet, mixins.CreateModelMixin):
    serializer_class = ContactPersonSerializer
    queryset = ContactPerson.objects.select_related('organization')
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = DefaultLimitPagination

    def create(self, request):
        if not request.user or not request.user.get_default_organization():
            return response.Response({'status': 'User without organization cannot POST contact persons.'},
                                     status=status.HTTP_403_FORBIDDEN)
        return super().create(request)
