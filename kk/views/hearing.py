import django_filters
from kk.models import Hearing, HearingComment, HearingImage
from kk.views.base import BaseImageSerializer
from kk.views.hearing_comment import HearingCommentSerializer
from kk.views.label import LabelSerializer
from kk.views.scenario import ScenarioFieldSerializer, ScenarioSerializer
from rest_framework import filters, permissions, serializers, status, viewsets
from rest_framework.decorators import detail_route
from rest_framework.response import Response


class HearingFilter(django_filters.FilterSet):
    next_closing = django_filters.DateTimeFilter(name='close_at', lookup_type='gt')

    class Meta:
        model = Hearing
        fields = ['next_closing', ]


class HearingImageSerializer(BaseImageSerializer):

    class Meta:
        model = HearingImage
        fields = ['title', 'url', 'width', 'height', 'caption']


class HearingSerializer(serializers.ModelSerializer):
    labels = LabelSerializer(many=True, read_only=True)
    images = HearingImageSerializer.get_field_serializer(many=True, read_only=True)
    scenarios = ScenarioFieldSerializer(many=True, read_only=True)
    comments = HearingCommentSerializer.get_field_serializer(many=True, read_only=True)

    class Meta:
        model = Hearing
        fields = ['abstract', 'heading', 'content', 'id', 'borough', 'n_comments',
                  'labels', 'close_at', 'created_at', 'latitude', 'longitude',
                  'servicemap_url', 'images', 'scenarios', 'images',
                  'closed', 'comments']


class HearingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for hearings.
    """
    queryset = Hearing.objects.all()
    serializer_class = HearingSerializer
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    # ordering_fields = ('created_at',)
    # ordering = ('-created_at',)
    # filter_class = HearingFilter

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
            serializer = HearingImageSerializer(page, many=True, context=self.get_serializer_context())
            return self.get_paginated_response(serializer.data)

        serializer = HearingImageSerializer(images, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @detail_route(methods=['get'])
    def scenarios(self, request, pk=None):
        hearing = self.get_object()
        scenarios = hearing.scenarios.all()

        page = self.paginate_queryset(scenarios)
        if page is not None:
            serializer = ScenarioSerializer(page, many=True, context=self.get_serializer_context())
            return self.get_paginated_response(serializer.data)

        serializer = ScenarioSerializer(scenarios, many=True, context=self.get_serializer_context())
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
