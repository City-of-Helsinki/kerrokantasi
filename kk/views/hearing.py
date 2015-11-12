import django_filters
from django.shortcuts import get_object_or_404
from rest_framework import filters, permissions, serializers, status, viewsets, response
from rest_framework.decorators import detail_route

from kk.models import Hearing, HearingComment, HearingImage
from kk.views.base import BaseImageSerializer
from kk.views.hearing_comment import HearingCommentSerializer
from kk.views.label import LabelSerializer
from kk.views.scenario import ScenarioFieldSerializer, ScenarioSerializer


class HearingFilter(django_filters.FilterSet):
    next_closing = django_filters.DateTimeFilter(name='close_at', lookup_type='gt')

    class Meta:
        model = Hearing
        fields = ['next_closing', ]


class HearingImageSerializer(BaseImageSerializer):
    class Meta:
        model = HearingImage
        fields = ['title', 'url', 'width', 'height', 'caption']


class HearingImageViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = HearingImageSerializer

    def get_queryset(self):
        hearing = get_object_or_404(Hearing, pk=self.kwargs["hearing_pk"])
        return hearing.images.all()


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

    @detail_route(methods=['post'])
    def follow(self, request, pk=None):
        hearing = self.get_object()

        # check if user already follow a hearing
        if Hearing.objects.filter(id=hearing.id, followers=request.user).exists():
            return response.Response({'status': 'Already follow'}, status=status.HTTP_304_NOT_MODIFIED)

        # add follower
        hearing.followers.add(request.user)

        # return success
        return response.Response({'status': 'You follow a hearing now'}, status=status.HTTP_201_CREATED)
