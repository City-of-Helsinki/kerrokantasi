import django_filters

from rest_framework import viewsets
from rest_framework import serializers
from rest_framework import filters

from kk.models import Hearing

class HearingFilter(django_filters.FilterSet):
    next_closing = django_filters.DateTimeFilter(name='close_at',lookup_type='gt')

    class Meta:
        model = Hearing
        fields = ['next_closing',]

class HearingSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Hearing

class HearingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for hearings.
    """
    queryset = Hearing.objects.all()
    serializer_class = HearingSerializer
    #filter_backends = (filters.OrderingFilter, )
    ordering_fields = ('created_at',)
    ordering = ('-created_at',)
    #filter_class = HearingFilter

    def get_queryset(self):
        next_closing = self.request.query_params.get('next_closing', None)
        if next_closing is not None:
            return self.queryset.filter(close_at__gt=next_closing).order_by('close_at')[:1]
        return self.queryset.order_by('-created_at')
        #return super(HearingViewSet, self).get_queryset()
