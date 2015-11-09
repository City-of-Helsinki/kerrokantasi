from rest_framework import serializers


class LabelSerializer(serializers.RelatedField):
    # Serializer for labels. Get label names instead of IDs.
    def to_representation(self, value):
        return value.label
