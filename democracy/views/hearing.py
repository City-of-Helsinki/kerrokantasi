import datetime
import django_filters
from collections import defaultdict
from django.conf import settings
from django.db import transaction
from django.db.models import Prefetch
from django.utils import timezone
from rest_framework import filters, permissions, response, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError
from rest_framework.settings import api_settings

from democracy.enums import InitialSectionType
from democracy.models import (
    ContactPerson,
    ContactPersonOrder,
    Hearing,
    Label,
    Organization,
    Project,
    Section,
    SectionImage,
)
from democracy.pagination import DefaultLimitPagination
from democracy.renderers import GeoJSONRenderer
from democracy.views.base import AdminsSeeUnpublishedMixin
from democracy.views.contact_person import ContactPersonSerializer
from democracy.views.hearing_report import HearingReport
from democracy.views.label import LabelSerializer
from democracy.views.project import ProjectCreateUpdateSerializer, ProjectFieldSerializer, ProjectSerializer
from democracy.views.reports_v2.hearing_report_powerpoint import HearingReportPowerPoint
from democracy.views.section import (
    SectionCreateUpdateSerializer,
    SectionFieldSerializer,
    SectionImageSerializer,
    SectionSerializer,
)
from democracy.views.utils import (
    GeoJSONField,
    GeometryBboxFilterBackend,
    NestedPKRelatedField,
    TranslatableSerializer,
    filter_by_hearing_visible,
    get_translation_list,
)


class HearingFilterSet(django_filters.rest_framework.FilterSet):
    open_at_lte = django_filters.IsoDateTimeFilter(field_name="open_at", lookup_expr="lte")
    open_at_gt = django_filters.IsoDateTimeFilter(field_name="open_at", lookup_expr="gt")
    title = django_filters.CharFilter(lookup_expr="icontains", field_name="translations__title", distinct=True)
    label = django_filters.Filter(
        field_name="labels__id", lookup_expr="in", distinct=True, widget=django_filters.widgets.CSVWidget
    )
    following = django_filters.BooleanFilter(method="filter_following")

    def filter_following(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(followers=self.request.user)
        return queryset

    class Meta:
        model = Hearing
        fields = ["published", "open_at_lte", "open_at_gt", "title", "label"]


class HearingCreateUpdateSerializer(serializers.ModelSerializer, TranslatableSerializer):
    geojson = GeoJSONField(required=False, allow_null=True)

    # this field is used only for incoming data validation, outgoing data is added manually
    # in to_representation()
    sections = serializers.ListField(child=serializers.DictField(), write_only=True)

    contact_persons = NestedPKRelatedField(
        queryset=ContactPerson.objects.all(), many=True, expanded=True, serializer=ContactPersonSerializer
    )
    labels = NestedPKRelatedField(queryset=Label.objects.all(), many=True, expanded=True, serializer=LabelSerializer)

    organization = serializers.SlugRelatedField(read_only=True, slug_field="name")
    project = serializers.DictField(write_only=True, required=False, allow_null=True)
    slug = serializers.SlugField()

    class Meta:
        model = Hearing
        fields = [
            "title",
            "id",
            "borough",
            "force_closed",
            "published",
            "open_at",
            "close_at",
            "created_at",
            "servicemap_url",
            "sections",
            "closed",
            "geojson",
            "organization",
            "slug",
            "contact_persons",
            "labels",
            "project",
        ]

    def __init__(self, *args, **kwargs):
        super(HearingCreateUpdateSerializer, self).__init__(*args, **kwargs)
        self.partial = kwargs.get("partial", False)

    def validate(self, data):
        data = super(HearingCreateUpdateSerializer, self).validate(data)
        action = self.context["view"].action
        titles = data.get("title")
        if not titles and action in ("create", "update"):
            raise serializers.ValidationError("Title is required at least in one locale")
        if titles and not any(titles.values()):
            # If title is present in payload, one locale must be set when creating,
            # updating as whole or patching
            raise serializers.ValidationError("Title is required at least in one locale")
        return data

    def _create_or_update_contact_persons(self, hearing, contact_person_data):
        """Preserve the order of contact persons in which they were sent to the API"""
        hearing.contact_persons.clear()
        for order, contact_person in enumerate(contact_person_data):
            ContactPersonOrder.objects.create(hearing=hearing, contact_person=contact_person, order=order)

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
            section_data["ordering"] = index
            pk = section_data.pop("id", None)

            serializer_params = {"data": section_data, "context": {"request": self.context["request"]}}

            if pk and not force_create:
                try:
                    section = hearing.sections.get(id=pk)
                    serializer_params["instance"] = section
                except Section.DoesNotExist:
                    pass

            serializer = SectionCreateUpdateSerializer(**serializer_params)

            try:
                serializer.is_valid(raise_exception=True)
            except ValidationError as e:
                errors = [{} for _ in range(len(sections_data))]
                errors[index] = e.detail
                raise ValidationError({"sections": errors})

            section = serializer.save(hearing=hearing)
            sections.add(section)
        return sections

    def _create_or_update_project(self, hearing, project_data):
        """
        Create or update project associated to a hearing.
        Handles the following cases:
            - Project is None
            - A new project with phases is created
            - An existing project with phases is used
            - An existing project with phases is used, but modified
        """
        if project_data is None:
            return None

        serializer_params = {
            "data": project_data,
            "context": {"hearing": hearing},
        }
        pk = project_data.pop("id", None)
        if pk is not None:
            # deserializing an existing instance
            try:
                serializer_params["instance"] = Project.objects.get(pk=pk)
            except Project.DoesNotExist:
                pass
        serializer = ProjectCreateUpdateSerializer(**serializer_params)
        serializer.is_valid(raise_exception=True)
        project = serializer.save()
        return project

    @transaction.atomic()
    def create(self, validated_data):
        contact_person_data = validated_data.pop("contact_persons", None)
        sections_data = validated_data.pop("sections")
        project_data = validated_data.pop("project", None)
        validated_data["organization"] = self.context["request"].user.get_default_organization()
        validated_data["created_by_id"] = self.context["request"].user.id
        validated_data["published"] = False  # Force new hearings to be unpublished initially
        hearing = super().create(validated_data)
        self._create_or_update_contact_persons(hearing, contact_person_data)
        self._create_or_update_sections(hearing, sections_data, force_create=True)
        self._create_or_update_project(hearing, project_data)
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
        if instance.organization not in self.context["request"].user.admin_organizations.all():
            raise PermissionDenied("Only organization admins can update organization hearings.")

        if self.partial:
            return super().update(instance, validated_data)

        contact_person_data = validated_data.pop("contact_persons", None)
        sections_data = validated_data.pop("sections")
        project_data = validated_data.pop("project", None)
        validated_data["modified_by_id"] = self.context["request"].user.id
        hearing = super().update(instance, validated_data)
        self._create_or_update_contact_persons(hearing, contact_person_data)
        sections = self._create_or_update_sections(hearing, sections_data)
        self._create_or_update_project(hearing, project_data)
        new_section_ids = set([section.id for section in sections])
        for section in hearing.sections.exclude(id__in=new_section_ids):
            for image in section.images.all():
                image.soft_delete()
            section.soft_delete()

        return hearing

    def validate_sections(self, data):
        if self.partial:
            raise ValidationError("Sections cannot be updated by PATCHing the Hearing")

        num_of_sections = defaultdict(int)

        for section_data in data:
            num_of_sections[section_data["type"]] += 1
            pk = section_data.get("id")

            if pk and self.instance and not self.instance.sections.filter(pk=pk).exists():
                raise ValidationError("The Hearing does not have a section with ID %s" % pk)

        if num_of_sections[InitialSectionType.MAIN] != 1:
            raise ValidationError("A hearing must have exactly one main section")

        if num_of_sections[InitialSectionType.CLOSURE_INFO] > 1:
            raise ValidationError("A hearing cannot have more than one closure info sections")

        return data

    def validate_project(self, data):
        if data is None:
            return data
        if len(self._get_active_phases(data)) != 1:
            raise ValidationError("Hearing in a project must have exactly one active phase")
        return data

    def _get_active_phases(self, project_data):
        """
        Return list of phase data marked as is_active in the project data
        """
        return [phase for phase in project_data["phases"] if phase["is_active"] is True]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["sections"] = SectionSerializer(instance=instance.sections.all(), many=True, context=self.context).data
        if instance.project_phase:
            data["project"] = ProjectSerializer(instance=instance.project_phase.project, context=self.context).data
        else:
            data["project"] = None
        return data


class HearingSerializer(serializers.ModelSerializer, TranslatableSerializer):
    labels = LabelSerializer(many=True, read_only=True)
    sections = serializers.SerializerMethodField()
    geojson = GeoJSONField()
    organization = serializers.SlugRelatedField(read_only=True, slug_field="name")
    main_image = serializers.SerializerMethodField()
    abstract = serializers.SerializerMethodField()
    preview_url = serializers.SerializerMethodField()
    contact_persons = ContactPersonSerializer(many=True, read_only=True)
    default_to_fullscreen = serializers.SerializerMethodField()
    project = serializers.SerializerMethodField()

    def _get_main_section(self, hearing):
        prefetched_mains = getattr(hearing, "main_section_list", [])
        return prefetched_mains[0] if prefetched_mains else hearing.get_main_section()

    def get_abstract(self, hearing):
        main_section = self._get_main_section(hearing)
        if not main_section:
            return ""
        translations = {
            t.language_code: t.abstract
            for t in get_translation_list(main_section, language_codes=self.Meta.translation_lang)
        }
        abstract = {}
        for lang_code, translation in translations.items():
            if translation:
                abstract[lang_code] = translation
        return abstract

    def get_sections(self, hearing):
        queryset = hearing.sections.select_related("type").prefetch_related("polls", "translations")
        if not hearing.closed:
            queryset = queryset.exclude(type__identifier=InitialSectionType.CLOSURE_INFO)

        serializer = SectionFieldSerializer(many=True, read_only=True)
        serializer.bind("sections", self)  # this is needed to get context in the serializer
        return serializer.to_representation(queryset)

    def get_main_image(self, hearing):
        main_section = self._get_main_section(hearing)
        if not main_section:
            return None

        main_image = main_section.images.first()
        if not main_image:
            return None

        if main_image.published or self.context["request"].user.is_superuser:
            return SectionImageSerializer(context=self.context, instance=main_image).data
        else:
            return None

    def get_default_to_fullscreen(self, hearing):
        main_section = self._get_main_section(hearing)
        return main_section.plugin_fullscreen if main_section else False

    def get_preview_url(self, hearing):
        is_public = hearing.published and hearing.open_at < timezone.now()
        if not is_public:
            return hearing.preview_url
        else:
            return None

    def get_project(self, hearing):
        if hearing.project_phase is None:
            return None
        context = self.context
        context["hearing"] = hearing
        project = hearing.project_phase.project
        serializer = ProjectFieldSerializer(read_only=True)
        serializer.bind("project", self)  # this is needed to get context in the serializer
        return serializer.to_representation(project)

    class Meta:
        model = Hearing
        fields = [
            "abstract",
            "title",
            "id",
            "borough",
            "n_comments",
            "published",
            "labels",
            "open_at",
            "close_at",
            "created_at",
            "servicemap_url",
            "sections",
            "preview_url",
            "project",
            "closed",
            "geojson",
            "organization",
            "slug",
            "main_image",
            "contact_persons",
            "default_to_fullscreen",
        ]
        read_only_fields = ["preview_url"]
        translation_lang = [lang["code"] for lang in settings.PARLER_LANGUAGES[None]]


class HearingListSerializer(HearingSerializer):
    def get_fields(self):
        fields = super(HearingListSerializer, self).get_fields()
        # Elide section, contact person and geo data when listing hearings; one can get to them via detail routes
        fields.pop("sections")
        fields.pop("contact_persons")
        request = self.context.get("request", None)
        if request:
            if not request.GET.get("include", None) == "geojson" and not isinstance(
                request.accepted_renderer, GeoJSONRenderer
            ):
                fields.pop("geojson")
        return fields


class HearingMapSerializer(serializers.ModelSerializer, TranslatableSerializer):
    geojson = GeoJSONField()

    class Meta:
        model = Hearing
        fields = ["id", "title", "borough", "open_at", "close_at", "closed", "geojson", "slug"]


hearing_prefetches = (
    Prefetch(
        "sections",
        queryset=Section.objects.filter(type__identifier="main").prefetch_related(
            Prefetch("translations", to_attr="translation_list"),
            Prefetch(
                "images",
                queryset=SectionImage.objects.filter(section__type__identifier="main").prefetch_related("translations"),
            ),
        ),
        to_attr="main_section_list",
    ),
    Prefetch("labels", queryset=Label.objects.prefetch_related("translations")),
    "translations",
)


class HearingViewSet(AdminsSeeUnpublishedMixin, viewsets.ModelViewSet):
    """
    API endpoint for hearings.
    """

    model = Hearing
    filter_backends = (
        django_filters.rest_framework.DjangoFilterBackend,
        filters.OrderingFilter,
        GeometryBboxFilterBackend,
    )
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    pagination_class = DefaultLimitPagination
    serializer_class = HearingListSerializer
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES + [
        GeoJSONRenderer,
    ]

    ordering_fields = ("created_at", "close_at", "open_at", "n_comments")
    ordering = ("-created_at",)
    filterset_class = HearingFilterSet

    def get_serializer_class(self, *args, **kwargs):
        if self.action == "list":
            return HearingListSerializer
        if self.action in ("create", "update", "partial_update"):
            return HearingCreateUpdateSerializer
        return HearingSerializer

    def filter_queryset(self, queryset):
        next_closing = self.request.query_params.get("next_closing", None)
        open = self.request.query_params.get("open", None)
        created_by = self.request.query_params.get("created_by", None)

        if created_by is not None and self.request.user:
            if created_by.lower() == "me":
                queryset = queryset.filter(created_by_id=self.request.user.id)
            else:
                try:
                    organizationObject = Organization.objects.get(name=created_by)
                except Organization.DoesNotExist:
                    organizationObject = None

                if organizationObject is not None:
                    queryset = queryset.filter(organization=organizationObject.id)

        if next_closing is not None:
            # sliced querysets cannot be filtered or ordered further
            return queryset.filter(close_at__gt=next_closing).order_by("close_at")[:1]
        if open is not None:
            if open.lower() == "false" or open == 0:
                queryset = (
                    queryset.filter(close_at__lt=datetime.datetime.now())
                    | queryset.filter(open_at__gt=datetime.datetime.now())
                    | queryset.filter(force_closed=True)
                ).distinct()
            else:
                queryset = (
                    queryset.filter(close_at__gt=datetime.datetime.now())
                    .filter(open_at__lt=datetime.datetime.now())
                    .filter(force_closed=False)
                )
        queryset = super().filter_queryset(queryset)
        return queryset

    def get_queryset(self):
        queryset = (
            filter_by_hearing_visible(Hearing.objects.with_unpublished(), self.request, hearing_lookup="")
            .select_related("organization", "project_phase__project")
            .prefetch_related(*hearing_prefetches)
        )

        return queryset

    def get_object(self):
        id_or_slug = self.kwargs[self.lookup_url_kwarg or self.lookup_field]

        queryset = self.filter_queryset(Hearing.objects.with_unpublished()).select_related(
            "organization", "project_phase__project"
        )
        queryset = queryset.prefetch_related(*hearing_prefetches)

        try:
            obj = queryset.get_by_id_or_slug(id_or_slug)
        except Hearing.DoesNotExist:
            raise NotFound()

        user = self.request.user

        preview_code = None
        if not obj.is_visible_for(user):
            preview_code = self.request.query_params.get("preview")
            if not preview_code or preview_code != obj.preview_code:
                raise NotFound()

        # require preview_code or superuser status to show a not yet opened hearing
        if not (preview_code or obj.is_visible_for(user)):
            raise NotFound()

        self.check_object_permissions(self.request, obj)
        return obj

    @action(detail=True, methods=["post"])
    def follow(self, request, pk=None):
        hearing = self.get_object()

        # check if user already follow a hearing
        if Hearing.objects.filter(id=hearing.id, followers=request.user).exists():
            return response.Response({"status": "Already follow"}, status=status.HTTP_304_NOT_MODIFIED)

        # add follower
        hearing.followers.add(request.user)

        # return success
        return response.Response({"status": "You follow a hearing now"}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def unfollow(self, request, pk=None):
        hearing = self.get_object()

        if Hearing.objects.filter(id=hearing.id, followers=request.user).exists():
            hearing.followers.remove(request.user)
            return response.Response({"status": "You stopped following a hearing"}, status=status.HTTP_204_NO_CONTENT)

        return response.Response({"status": "You are not following this hearing"}, status=status.HTTP_304_NOT_MODIFIED)

    @action(detail=True, methods=["get"])
    def report(self, request, pk=None):
        context = self.get_serializer_context()
        report = HearingReport(HearingSerializer(self.get_object(), context=context).data, context=context)
        return report.get_response()

    @action(detail=True, methods=["get"])
    def report_pptx(self, request, pk=None):
        user = request.user
        if not user or not user.is_authenticated or not user.get_default_organization():
            return response.Response(
                {"status": "User without organization cannot GET report pptx."}, status=status.HTTP_403_FORBIDDEN
            )
        context = self.get_serializer_context()
        report = HearingReportPowerPoint(HearingSerializer(self.get_object(), context=context).data, context=context)
        return report.get_response()

    @action(detail=False, methods=["get"])
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
            return response.Response(
                {"status": "User without organization cannot POST hearings."}, status=status.HTTP_403_FORBIDDEN
            )
        return super().create(request)

    def update(self, request, pk=None, partial=False):
        if not request.user or not request.user.get_default_organization():
            return response.Response(
                {"status": "User without organization cannot PUT hearings."}, status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, pk=pk, partial=partial)

    def destroy(self, request, pk=None):
        if not request.user or not request.user.get_default_organization():
            return response.Response(
                {"status": "User without organization cannot DELETE hearings."}, status=status.HTTP_403_FORBIDDEN
            )
        hearing = self.get_object()
        if hearing.published:
            return response.Response({"status": "Cannot DELETE published hearing."}, status=status.HTTP_403_FORBIDDEN)
        if hearing.n_comments > 0:
            return response.Response(
                {"status": "Cannot DELETE hearing with comments."}, status=status.HTTP_403_FORBIDDEN
            )
        hearing.soft_delete(user=request.user)
        return response.Response({"status": "Hearing deleted"}, status=status.HTTP_200_OK)
