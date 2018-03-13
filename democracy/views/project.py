
# -*- coding: utf-8 -*-

from rest_framework import permissions
from rest_framework import response
from rest_framework import serializers, viewsets, filters, mixins
import django_filters
from rest_framework import status

from democracy.models import Project, ProjectPhase
from democracy.pagination import DefaultLimitPagination
from democracy.views.utils import TranslatableSerializer, NestedPKRelatedField


class ProjectPhaseSerializer(serializers.ModelSerializer, TranslatableSerializer):
    has_hearings = serializers.SerializerMethodField()

    class Meta:
        model = ProjectPhase
        fields = ('id', 'description', 'has_hearings', 'ordering', 'schedule', 'title', )

    def get_has_hearings(self, project_phase):
        #return self.hearings.exists()
        return False


class ProjectSerializer(serializers.ModelSerializer, TranslatableSerializer):
    phases = NestedPKRelatedField(queryset=ProjectPhase.objects.all(), many=True, expanded=True, serializer=ProjectPhaseSerializer)

    class Meta:
        model = Project
        fields = ('id', 'identifier', 'title', 'phases')


class ProjectViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProjectSerializer
    queryset = Project.objects.all()
    pagination_class = DefaultLimitPagination
    #permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

