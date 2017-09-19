from collections import defaultdict
import django_filters
import datetime

from django.conf import settings
from django.db import transaction
from django.db.models import Prefetch
from rest_framework import filters, permissions, response, serializers, status, viewsets
from rest_framework.decorators import detail_route, list_route
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.fields import JSONField
from rest_framework.settings import api_settings

from democracy.enums import InitialSectionType
from democracy.models import ContactPerson, Hearing, Label, Section, SectionImage
from democracy.pagination import DefaultLimitPagination
from democracy.renderers import GeoJSONRenderer
from democracy.views.base import AdminsSeeUnpublishedMixin
from democracy.views.contact_person import ContactPersonSerializer
from democracy.views.label import LabelSerializer
from democracy.views.section import (
    SectionCreateUpdateSerializer, SectionFieldSerializer, SectionImageSerializer, SectionSerializer
)
from democracy.views.utils import TranslatableSerializer
from .hearing_report import HearingReport
from .utils import NestedPKRelatedField, filter_by_hearing_visible


class HearingFilter(django_filters.FilterSet):
    open_at_lte = django_filters.IsoDateTimeFilter(name='open_at', lookup_expr='lte')
    open_at_gt = django_filters.IsoDateTimeFilter(name='open_at', lookup_expr='gt')
    title = django_filters.CharFilter(lookup_expr='icontains', name='translations__title', distinct=True)
    label = django_filters.Filter(name='labels__id', lookup_expr='in', distinct=True,
                                  widget=django_filters.widgets.CSVWidget)

    class Meta:
        model = Hearing
        fields = ['published', 'open_at_lte', 'open_at_gt', 'title', 'label']


class HearingCreateUpdateSerializer(serializers.ModelSerializer, TranslatableSerializer):
    geojson = JSONField(required=False, allow_null=True)

    # this field is used only for incoming data validation, outgoing data is added manually
    # in to_representation()
    sections = serializers.ListField(child=serializers.DictField(), write_only=True)

    contact_persons = NestedPKRelatedField(queryset=ContactPerson.objects.all(), many=True, expanded=True,
                                           serializer=ContactPersonSerializer)
    labels = NestedPKRelatedField(queryset=Label.objects.all(), many=True, expanded=True, serializer=LabelSerializer)

    organization = serializers.SlugRelatedField(
        read_only=True,
        slug_field='name'
    )

    class Meta:
        model = Hearing
        fields = [
            'title', 'id', 'borough', 'force_closed',
            'published', 'open_at', 'close_at', 'created_at',
            'servicemap_url', 'sections',
            'closed', 'geojson', 'organization', 'slug',
            'contact_persons', 'labels',
        ]

    def __init__(self, *args, **kwargs):
        super(HearingCreateUpdateSerializer, self).__init__(*args, **kwargs)
        self.partial = kwargs.get('partial', False)

    def _create_or_update_sections(self, hearing, sections_data, force_create=False):
        """
        Create or update sections of a hearing

        :param hearing: The hearing
        :type hearing: democracy.models.Hearing

        :param sections_data: The list of serialized sections to create or update
        :type sections_data: list of dictionaries

        :param force_create: Boolean to force the creation of new sections despite
                             the presences of section ID.
        :type force_create: Boolean

        :return: The set of the newly created/updated sections
        :rtype: Set of democracy.models.Section
        """
        sections = set()
        for index, section_data in enumerate(sections_data):
            section_data['ordering'] = index
            pk = section_data.pop('id', None)

            serializer_params = {
                'data': section_data,
            }

            if pk and not force_create:
                try:
                    section = hearing.sections.get(id=pk)
                    serializer_params['instance'] = section
                except Section.DoesNotExist:
                    pass

            serializer = SectionCreateUpdateSerializer(**serializer_params)

            try:
                serializer.is_valid(raise_exception=True)
            except ValidationError as e:
                errors = [{} for _ in range(len(sections_data))]
                errors[index] = e.detail
                raise ValidationError({'sections': errors})

            section = serializer.save(hearing=hearing)
            sections.add(section)
        return sections

    @transaction.atomic()
    def create(self, validated_data):
        sections_data = validated_data.pop('sections')
        validated_data['organization'] = self.context['request'].user.get_default_organization()
        hearing = super().create(validated_data)
        self._create_or_update_sections(hearing, sections_data, force_create=True)
        return hearing

    @transaction.atomic()
    def update(self, instance, validated_data):
        """
        Handle Hearing update and it's sections create/update/delete.

        Sections are matched by their ids:
          * If an id isn't given or it doesn't exist, create a new section (ignoring given id).
          * If a section with given id exists, update it.
          * Old sections whose ids aren't matched are (soft) deleted.
        """
        if instance.organization not in self.context['request'].user.admin_organizations.all():
            raise PermissionDenied('Only organization admins can update organization hearings.')

        if self.partial:
            return super().update(instance, validated_data)

        sections_data = validated_data.pop('sections')
        hearing = super().update(instance, validated_data)
        sections = self._create_or_update_sections(hearing, sections_data)
        new_section_ids = set([section.id for section in sections])
        for section in hearing.sections.exclude(id__in=new_section_ids):
            for image in section.images.all():
                image.soft_delete()
            section.soft_delete()

        return hearing

    def validate_sections(self, data):
        if self.partial:
            raise ValidationError('Sections cannot be updated by PATCHing the Hearing')

        num_of_sections = defaultdict(int)

        for section_data in data:
            num_of_sections[section_data['type']] += 1
            pk = section_data.get('id')

            if pk and self.instance and not self.instance.sections.filter(pk=pk).exists():
                raise ValidationError('The Hearing does not have a section with ID %s' % pk)

        if num_of_sections[InitialSectionType.MAIN] != 1:
            raise ValidationError('A hearing must have exactly one main section')

        if num_of_sections[InitialSectionType.CLOSURE_INFO] > 1:
            raise ValidationError('A hearing cannot have more than one closure info sections')

        return data

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['sections'] = SectionSerializer(
            instance=instance.sections.all(),
            many=True,
            context=self.context
        ).data
        return data


class HearingSerializer(serializers.ModelSerializer, TranslatableSerializer):
    labels = LabelSerializer(many=True, read_only=True)
    sections = serializers.SerializerMethodField()
    geojson = JSONField()
    organization = serializers.SlugRelatedField(
        read_only=True,
        slug_field='name'
    )
    main_image = serializers.SerializerMethodField()
    abstract = serializers.SerializerMethodField()
    contact_persons = ContactPersonSerializer(many=True, read_only=True)
    default_to_fullscreen = serializers.SerializerMethodField()

    def _get_main_section(self, hearing):
        prefetched_mains = getattr(hearing, 'main_section_list', [])
        return prefetched_mains[0] if prefetched_mains else hearing.get_main_section()

    def get_abstract(self, hearing):
        main_section = self._get_main_section(hearing)
        if not main_section:
            return ''
        translations = {
            t.language_code: t.abstract for t in
            main_section.translations.filter(language_code__in=self.Meta.translation_lang)
        }
        abstract = {}
        for lang_code, translation in translations.items():
            if translation:
                abstract[lang_code] = translation
        return abstract

    def get_sections(self, hearing):
        queryset = hearing.sections.all()
        if not hearing.closed:
            queryset = queryset.exclude(type__identifier=InitialSectionType.CLOSURE_INFO)

        serializer = SectionFieldSerializer(many=True, read_only=True)
        serializer.bind('sections', self)  # this is needed to get context in the serializer
        return serializer.to_representation(queryset)

    def get_main_image(self, hearing):
        main_image = SectionImage.objects.filter(
            section__hearing=hearing,
            section__type__identifier='main'
        ).first()

        if not main_image:
            return None

        if main_image.published or self.context['request'].user.is_superuser:
            return SectionImageSerializer(context=self.context, instance=main_image).data
        else:
            return None

    def get_default_to_fullscreen(self, hearing):
        main_section = self._get_main_section(hearing)
        return main_section.plugin_fullscreen if main_section else False

    class Meta:
        model = Hearing
        fields = [
            'abstract', 'title', 'id', 'borough', 'n_comments',
            'published', 'labels', 'open_at', 'close_at', 'created_at',
            'servicemap_url', 'sections',
            'closed', 'geojson', 'organization', 'slug', 'main_image', 'contact_persons', 'default_to_fullscreen',
        ]
        translation_lang = [lang['code'] for lang in settings.PARLER_LANGUAGES[None]]


class HearingListSerializer(HearingSerializer):

    def get_fields(self):
        fields = super(HearingListSerializer, self).get_fields()
        # Elide section and geo data when listing hearings; one can get to them via detail routes
        fields.pop("sections")
        request = self.context.get('request', None)
        if request:
            if not request.GET.get('include', None) == 'geojson'\
                    and not isinstance(request.accepted_renderer, GeoJSONRenderer):
                fields.pop("geojson")
        return fields


class HearingMapSerializer(serializers.ModelSerializer, TranslatableSerializer):
    geojson = JSONField()

    class Meta:
        model = Hearing
        fields = [
            'id', 'title', 'borough', 'open_at', 'close_at', 'closed', 'geojson', 'slug'
        ]


class HearingViewSet(AdminsSeeUnpublishedMixin, viewsets.ModelViewSet):
    """
    API endpoint for hearings.
    """
    model = Hearing
    filter_backends = (filters.DjangoFilterBackend, filters.OrderingFilter)
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = DefaultLimitPagination
    serializer_class = HearingListSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + [GeoJSONRenderer, ]

    ordering_fields = ('created_at', 'close_at', 'open_at', 'n_comments')
    ordering = ('-created_at',)
    filter_class = HearingFilter

    def get_serializer_class(self, *args, **kwargs):
        if self.action == 'list':
            return HearingListSerializer
        if self.action in ('create', 'update', 'partial_update'):
            return HearingCreateUpdateSerializer

        return HearingSerializer

    def filter_queryset(self, queryset):
        next_closing = self.request.query_params.get('next_closing', None)
        open = self.request.query_params.get('open', None)
        if next_closing is not None:
            # sliced querysets cannot be filtered or ordered further
            return queryset.filter(close_at__gt=next_closing).order_by('close_at')[:1]
        if open is not None:
            if open.lower() == 'false' or open == 0:
                queryset = (queryset.filter(close_at__lt=datetime.datetime.now()) |
                            queryset.filter(open_at__gt=datetime.datetime.now()) |
                            queryset.filter(force_closed=True)).distinct()
            else:
                queryset = queryset.filter(close_at__gt=datetime.datetime.now()).\
                    filter(open_at__lt=datetime.datetime.now()).filter(force_closed=False)
        queryset = super().filter_queryset(queryset)
        return queryset

    def get_queryset(self):
        queryset = filter_by_hearing_visible(Hearing.objects.with_unpublished(), self.request,
                                             hearing_lookup='').prefetch_related(
            Prefetch(
                'sections',
                queryset=Section.objects.filter(type__identifier='main'),
                to_attr='main_section_list'
            )
        )
        return queryset

    def get_object(self):
        id_or_slug = self.kwargs[self.lookup_url_kwarg or self.lookup_field]

        queryset = self.filter_queryset(Hearing.objects.with_unpublished())
        queryset = queryset.prefetch_related(
            Prefetch(
                'sections',
                queryset=Section.objects.filter(type__identifier='main'),
                to_attr='main_section_list'
            )
        )

        try:
            obj = queryset.get_by_id_or_slug(id_or_slug)
        except Hearing.DoesNotExist:
            raise NotFound()

        user = self.request.user

        preview_code = None
        if not obj.is_visible_for(user):
            preview_code = self.request.query_params.get('preview')
            if not preview_code or preview_code != obj.preview_code:
                raise NotFound()

        # require preview_code or superuser status to show a not yet opened hearing
        if not (preview_code or obj.is_visible_for(user)):
            raise NotFound()

        self.check_object_permissions(self.request, obj)
        return obj

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

    @detail_route(methods=['post'])
    def unfollow(self, request, pk=None):
        hearing = self.get_object()

        if Hearing.objects.filter(id=hearing.id, followers=request.user).exists():
            hearing.followers.remove(request.user)
            return response.Response({'status': 'You stopped following a hearing'}, status=status.HTTP_204_NO_CONTENT)

        return response.Response({'status': 'You are not following this hearing'}, status=status.HTTP_304_NOT_MODIFIED)

    @detail_route(methods=['get'])
    def report(self, request, pk=None):
        context = self.get_serializer_context()
        report = HearingReport(HearingSerializer(self.get_object(), context=context).data, context=context)
        return report.get_response()

    @list_route(methods=['get'])
    def map(self, request):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = HearingMapSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = HearingMapSerializer(queryset, many=True)
        return response.Response(serializer.data)

    def create(self, request):
        if not request.user or not request.user.get_default_organization():
            return response.Response({'status': 'User without organization cannot POST hearings.'},
                                     status=status.HTTP_403_FORBIDDEN)
        return super().create(request)

    def update(self, request, pk=None, partial=False):
        if not request.user or not request.user.get_default_organization():
            return response.Response({'status': 'User without organization cannot PUT hearings.'},
                                     status=status.HTTP_403_FORBIDDEN)
        return super().update(request, pk=pk, partial=partial)
