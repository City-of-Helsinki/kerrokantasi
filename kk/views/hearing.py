from rest_framework import viewsets
from rest_framework import serializers

from kk.models import Hearing

class HearingSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Hearing

class HearingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for hearings.
    """
    queryset = Hearing.objects.all()
    serializer_class = HearingSerializer
