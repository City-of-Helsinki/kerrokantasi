# -*- coding: utf-8 -*-
import django_filters
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.encoding import force_text
from rest_framework import permissions, response, serializers, status, viewsets
from rest_framework.decorators import detail_route
from rest_framework.settings import api_settings
from reversion import revisions

from democracy.models.comment import BaseComment
from democracy.views.base import AdminsSeeUnpublishedMixin, CreatedBySerializer
from democracy.views.utils import GeoJSONField, AbstractSerializerMixin
from democracy.renderers import GeoJSONRenderer

COMMENT_FIELDS = ['id', 'content', 'author_name', 'n_votes', 'created_at', 'is_registered', 'can_edit',
                  'geojson', 'map_comment_text','images', 'label', 'organization']


class BaseCommentSerializer(AbstractSerializerMixin, CreatedBySerializer, serializers.ModelSerializer):
    is_registered = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    organization = serializers.SerializerMethodField()
    geojson = GeoJSONField()

    def to_representation(self, instance):
        r = super().to_representation(instance)
        request = self.context.get('request', None)
        if request:
            if request.GET.get('include', None) == 'plugin_data':
                r['plugin_data'] = instance.plugin_data
        return r

    def get_is_registered(self, obj):
        return obj.created_by_id is not None

    def get_can_edit(self, obj):
        request = self.context.get('request', None)
        if request:
            return obj.can_edit(request)
        return False

    def get_organization(self, obj):
        if obj.organization:
            return str(obj.organization)
        return None

    class Meta:
        model = BaseComment
        fields = COMMENT_FIELDS


class BaseCommentFilterSet(django_filters.rest_framework.FilterSet):
    authorization_code = django_filters.CharFilter()

    class Meta:
        model = BaseComment
        fields = ['authorization_code', ]


class BaseCommentViewSet(AdminsSeeUnpublishedMixin, viewsets.ModelViewSet):
    """
    Base viewset for comments.
    """
    permission_classes = (permissions.AllowAny,)
    serializer_class = None
    edit_serializer_class = None
    filter_backends = (django_filters.rest_framework.DjangoFilterBackend,)
    filterset_class = BaseCommentFilterSet
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + [GeoJSONRenderer, ]

    def get_serializer(self, *args, **kwargs):
        serializer_class = kwargs.pop("serializer_class", None) or self.get_serializer_class()
        context = kwargs['context'] = self.get_serializer_context()
        if serializer_class is self.edit_serializer_class and "data" in kwargs:  # Creating things with data?
            # So inject a reference to the parent object
            data = kwargs["data"].copy()
            data[serializer_class.Meta.model.parent_field] = context["comment_parent"]
            kwargs["data"] = data
        return serializer_class(*args, **kwargs)

    def get_comment_parent_id(self):
        # this is introduced to kwargs directly from URL!
        return self.kwargs.get("comment_parent_pk", None)

    def get_comment_parent(self):
        """
        :rtype: Commentable
        """
        return self.get_queryset().model.parent_model.objects.get(pk=self.get_comment_parent_id())

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["comment_parent"] = self.get_comment_parent_id()
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(**{queryset.model.parent_field: self.get_comment_parent_id()})

    def create_related(self, request, instance=None, *args, **kwargs):
        pass

    def update_related(self, request, instance=None, *args, **kwargs):
        pass

    def _check_may_comment(self, request):
        parent = self.get_comment_parent()
        try:
            # The `assert` checks that the function adheres to the protocol defined in `Commenting`.
            assert parent.check_commenting(request) is None
        except ValidationError as verr:
            return response.Response(
                {'status': force_text(verr), 'code': verr.code},
                status=status.HTTP_403_FORBIDDEN
            )

    def _check_may_vote(self, request):
        parent = self.get_comment_parent()
        try:
            # The `assert` checks that the function adheres to the protocol defined in `Commenting`.
            assert parent.check_voting(request) is None
        except ValidationError as verr:
            return response.Response(
                {'status': force_text(verr), 'code': verr.code},
                status=status.HTTP_403_FORBIDDEN
            )

    def create(self, request, *args, **kwargs):
        resp = self._check_may_comment(request)
        if resp:
            return resp

        # Use one serializer for creation,
        serializer = self.get_serializer(serializer_class=self.edit_serializer_class, data=request.data)
        serializer.is_valid(raise_exception=True)
        kwargs = {}
        if self.request.user.is_authenticated:
            kwargs['created_by'] = self.request.user
        comment = serializer.save(**kwargs)
        # and another for the response
        serializer = self.get_serializer(instance=comment)
        self.create_related(request, instance=comment, *args, **kwargs)
        return response.Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        resp = self._check_may_comment(request)
        if resp:
            return resp

        instance = self.get_object()
        if self.request.user != instance.created_by:
            return response.Response(
                {'status': 'You may not edit a comment not owned by you'},
                status=status.HTTP_403_FORBIDDEN
            )
        if request.user.is_authenticated and 'author_name' in request.data:
            if request.data['author_name'] != instance.author_name:
                return response.Response(
                    {'status': 'Authenticated users cannot set author name.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        # Use one serializer for update,
        partial = kwargs.pop('partial', False)
        serializer = self.get_serializer(instance=instance,
                                         serializer_class=self.edit_serializer_class,
                                         data=request.data,
                                         partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        instance.refresh_from_db()

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        # and another for the response
        serializer = self.get_serializer(instance=instance)
        self.update_related(request, instance=instance, *args, **kwargs)
        return response.Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        resp = self._check_may_comment(request)
        if resp:
            return resp

        instance = self.get_object()

        if self.request.user != instance.created_by:
            return response.Response(
                {'status': 'You may not delete a comment not owned by you'},
                status=status.HTTP_403_FORBIDDEN
            )

        instance.soft_delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)

    def perform_update(self, serializer):
        with transaction.atomic(), revisions.create_revision():
            super().perform_update(serializer)

    @detail_route(methods=['post'])
    def vote(self, request, **kwargs):
        resp = self._check_may_vote(request)
        if resp:
            return resp
        comment = self.get_object()

        if not request.user.is_authenticated:
            # If the check went through, anonymous voting is allowed
            comment.n_unregistered_votes += 1
            comment.recache_n_votes()
            return response.Response({'status': 'Vote has been counted'}, status=status.HTTP_200_OK)
        # Check if user voted already. If yes, return 304.
        if comment.__class__.objects.filter(id=comment.id, voters=request.user).exists():
            return response.Response({'status': 'Already voted'}, status=status.HTTP_304_NOT_MODIFIED)
        # add voter
        comment.voters.add(request.user)
        # update number of votes
        comment.recache_n_votes()
        # return success
        return response.Response({'status': 'Vote has been added'}, status=status.HTTP_201_CREATED)

    @detail_route(methods=['post'])
    def unvote(self, request, **kwargs):
        # Return 403 if user is not authenticated
        if not request.user.is_authenticated:
            return response.Response({'status': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        comment = self.get_object()

        # Check if user voted already. If yes, return 400.
        if comment.__class__.objects.filter(id=comment.id, voters=request.user).exists():
            # remove voter
            comment.voters.remove(request.user)
            # update number of votes
            comment.recache_n_votes()
            # return success
            return response.Response({'status': 'Removed vote'}, status=status.HTTP_204_NO_CONTENT)

        return response.Response({'status': 'You have not voted for this comment'}, status=status.HTTP_304_NOT_MODIFIED)
