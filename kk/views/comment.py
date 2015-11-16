# -*- coding: utf-8 -*-
import reversion

from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework.decorators import detail_route
from rest_framework import permissions, response, serializers, status, viewsets

from kk.models.comment import BaseComment
from kk.views.base import CreatedBySerializer
from kk.views.utils import AbstractSerializerMixin


class BaseCommentSerializer(AbstractSerializerMixin, CreatedBySerializer, serializers.ModelSerializer):

    class Meta:
        model = BaseComment
        fields = ['content', 'votes', 'created_by', 'created_at']


class BaseCommentViewSet(viewsets.ModelViewSet):
    """
    Base viewset for comments.
    """
    permission_classes = (permissions.AllowAny,)
    serializer_class = None
    create_serializer_class = None

    def get_serializer(self, *args, **kwargs):
        serializer_class = kwargs.pop("serializer_class", None) or self.get_serializer_class()
        context = kwargs['context'] = self.get_serializer_context()
        if serializer_class is self.create_serializer_class:  # Creating things?
            if "data" in kwargs:  # With data, too?!
                # So inject a reference to the parent object
                comment_model = serializer_class.Meta.model
                # parent_obj = get_object_or_404(comment_model.parent_model, pk=)
                kwargs["data"][comment_model.parent_field] = context["comment_parent"]
        return serializer_class(*args, **kwargs)

    def get_comment_parent_id(self):
        return self.kwargs["comment_parent_pk"]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context["comment_parent"] = self.get_comment_parent_id()
        return context

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(**{queryset.model.parent_field: self.get_comment_parent_id()})

    def create(self, request, *args, **kwargs):
        # Use one serializer for creation,
        serializer = self.get_serializer(serializer_class=self.create_serializer_class, data=request.data)
        serializer.is_valid(raise_exception=True)
        kwargs = {}
        if self.request._request.user.is_authenticated():
            kwargs['created_by'] = self.request._request.user
        comment = serializer.save(**kwargs)
        # and another for the response
        serializer = self.get_serializer(instance=comment)
        return response.Response(serializer.data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        with transaction.atomic(), reversion.create_revision():
            super().perform_update(serializer)

    @detail_route(methods=['post'])
    def vote(self, request, **kwargs):
        # Return 403 if user is not authenticated
        if not request.user.is_authenticated():
            return response.Response({'status': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

        comment = self.get_object()

        # Check if user voted already. If yes, return 400.
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
        if not request.user.is_authenticated():
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