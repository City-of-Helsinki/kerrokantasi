from rest_framework import viewsets

from kk.models import Hearing

class HearingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for hearings.
    """
    queryset = Hearing.objects.all()
