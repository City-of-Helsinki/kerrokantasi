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

# Serializer for labels. Get label names instead of IDs.
class LabelSerializer(serializers.RelatedField):
    def to_representation(self, value):
        return  value.label

class HearingSerializer(serializers.ModelSerializer):
    labels = LabelSerializer(many=True, read_only=True)

    class Meta:
        model = Hearing
        fields = ['abstract', 'heading', 'borough', 'n_comments', 'labels', 'close_at', 'created_at',]

class HearingViewSet(viewsets.ModelViewSet):
    """
    API endpoint for hearings.
    """
    queryset = Hearing.objects.all()
    serializer_class = HearingSerializer
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter)
    #ordering_fields = ('created_at',)
    #ordering = ('-created_at',)
    #filter_class = HearingFilter

    def get_queryset(self):
        next_closing = self.request.query_params.get('next_closing', None)
        if next_closing is not None:
            return self.queryset.filter(close_at__gt=next_closing).order_by('close_at')[:1]
        return self.queryset.order_by('-created_at')

    # temporary for query debug purpose
    def _list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        print (queryset.query)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
