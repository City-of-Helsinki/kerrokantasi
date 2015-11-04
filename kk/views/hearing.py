import django_filters

from rest_framework import viewsets
from rest_framework import serializers
from rest_framework import filters
from rest_framework.decorators import detail_route
from rest_framework.response import Response

from kk.models import Hearing

from .image import ImageFieldSerializer, ImageSerializer
from .introduction import IntroductionFieldSerializer, IntroductionSerializer
from .scenario import ScenarioFieldSerializer, ScenarioSerializer


class HearingFilter(django_filters.FilterSet):
    next_closing = django_filters.DateTimeFilter(name='close_at', lookup_type='gt')

    class Meta:
        model = Hearing
        fields = ['next_closing', ]

# Serializer for labels. Get label names instead of IDs.


class LabelSerializer(serializers.RelatedField):

    def to_representation(self, value):
        return value.label


class HearingSerializer(serializers.ModelSerializer):
    labels = LabelSerializer(many=True, read_only=True)
    images = ImageFieldSerializer(many=True, read_only=True)
    introductions = IntroductionFieldSerializer(many=True, read_only=True)
    scenarios = ScenarioFieldSerializer(many=True, read_only=True)

    class Meta:
        model = Hearing
        fields = ['abstract', 'heading', 'content', 'id', 'borough', 'n_comments',
                'labels', 'close_at', 'created_at', 'latitude', 'longitude',
                'servicemap_url', 'images', 'introductions', 'scenarios', 'images',
                'closed']


class HearingViewSet(viewsets.ReadOnlyModelViewSet):
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

    @detail_route(methods=['get'])
    def images(self, request, pk=None):
        hearing = self.get_object()
        images = hearing.images.all()

        page = self.paginate_queryset(images)
        if page is not None:
            serializer = ImageSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ImageSerializer(images, many=True)
        return Response(serializer.data)

    @detail_route(methods=['get'])
    def introductions(self, request, pk=None):
        hearing = self.get_object()
        intros = hearing.introductions.all()

        page = self.paginate_queryset(intros)
        if page is not None:
            serializer = IntroductionSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = IntroductionSerializer(intros, many=True)
        return Response(serializer.data)

    @detail_route(methods=['get'])
    def scenarios(self, request, pk=None):
        hearing = self.get_object()
        scenarios = hearing.scenarios.all()

        page = self.paginate_queryset(scenarios)
        if page is not None:
            serializer = ScenarioSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = ScenarioSerializer(scenarios, many=True)
        return Response(serializer.data)

    # temporary for query debug purpose
    def _list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        print(queryset.query)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
