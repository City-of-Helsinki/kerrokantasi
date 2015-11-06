from rest_framework import serializers


# Serializer for user field


class UserFieldSerializer(serializers.ModelSerializer):

    def to_representation(self, user):
        return user.username


# Serializer for created_by


class CreatedBySerializer(serializers.ModelSerializer):

    created_by = UserFieldSerializer()
