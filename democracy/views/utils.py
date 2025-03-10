import base64
import json
from collections import OrderedDict
from operator import attrgetter

from django.conf import settings
from django.contrib.gis.gdal.error import GDALException
from django.contrib.gis.geos import GeometryCollection, GEOSGeometry
from django.core.files.base import ContentFile
from django.db.models import Q
from django.utils.crypto import get_random_string
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from munigeo.api import build_bbox_filter, srid_to_srs
from rest_framework import serializers
from rest_framework.exceptions import ParseError, ValidationError
from rest_framework.filters import BaseFilterBackend
from rest_framework.relations import (
    MANY_RELATION_KWARGS,
    ManyRelatedField,
    PrimaryKeyRelatedField,
)
from rest_framework.utils import encoders


def get_translation_list(obj, language_codes=None):
    """
    This method uses translation_list attribute created by Prefetch to obtain translations without database hit.

    :param obj: Any translated object that may have had Prefetch('translations', to_attr='translation_list') done
    :param language_codes: Iterable containing the languages to return
    :return: QuerySet or list containing the desired translations, if not the default
    """  # noqa: E501
    if language_codes is None:
        language_codes = [lang["code"] for lang in settings.PARLER_LANGUAGES[None]]
    prefetched_translations = getattr(obj, "translation_list", [])
    filtered_prefetched = [
        translation
        for translation in prefetched_translations
        if translation.language_code in language_codes
    ]
    return (
        filtered_prefetched
        if prefetched_translations
        else obj.translations.filter(language_code__in=language_codes)
    )


def compare_serialized(a, b):
    a = json.dumps(a, cls=encoders.JSONEncoder, sort_keys=True)
    b = json.dumps(b, cls=encoders.JSONEncoder, sort_keys=True)
    return a == b


class AbstractFieldSerializer(serializers.RelatedField):
    parent_serializer_class = serializers.ModelSerializer
    many_field_class = ManyRelatedField

    def to_representation(self, image):
        return self.parent_serializer_class(image, context=self.context).data

    @classmethod
    def many_init(cls, *args, **kwargs):
        list_kwargs = {"child_relation": cls(*args, **kwargs)}
        for key in kwargs.keys():
            if key in MANY_RELATION_KWARGS:
                list_kwargs[key] = kwargs[key]
        return cls.many_field_class(**list_kwargs)


def filter_by_hearing_visible(
    queryset, request, hearing_lookup="hearing", include_orphans=False
):
    if hearing_lookup:
        hearing_lookup = "%s__" % hearing_lookup

    filters = {
        "%sdeleted" % hearing_lookup: False,
    }
    user = request.user

    if user.is_superuser:
        q = Q(**filters)
        if include_orphans:
            q |= Q(**{"%sisnull" % hearing_lookup: True})
        return queryset.filter(q)

    filters["%spublished" % hearing_lookup] = True
    filters["%sopen_at__lte" % hearing_lookup] = now()
    q = Q(**filters)

    if user.is_authenticated:
        organizations = user.admin_organizations.all()
        if organizations.exists():
            # regardless of publication status or date, admins will see everything
            # from their organization
            q |= Q(**{"%sorganization__in" % hearing_lookup: organizations})
        if include_orphans:
            # include items belonging to no hearings
            q |= Q(**{"%sisnull" % hearing_lookup: True})

    return queryset.filter(q)


class NestedPKRelatedField(PrimaryKeyRelatedField):
    """
    Support of showing and saving of expanded nesting or just a resource ID.

    The keyword argument 'expanded' defines whether the nested object is expanded or not.
    Default serializing is expanded=false.
    """  # noqa: E501

    invalid_format_error = _(
        "Incorrect format. Expected dictionary, received %(data)s."
    )
    missing_id_error = _(
        'The primary key is missing. Expected {"id": id, ...}, received %(data)s.'
    )

    def __init__(self, *args, **kwargs):
        self.related_serializer = kwargs.pop("serializer", None)
        self.expanded = bool(kwargs.pop("expanded", False))
        super(NestedPKRelatedField, self).__init__(*args, **kwargs)

    def use_pk_only_optimization(self):
        return not self.expanded

    def to_representation(self, obj):
        if self.expanded:
            return self.related_serializer(obj, context=self.context).data
        id = super(NestedPKRelatedField, self).to_representation(obj)
        if id is None:
            return None
        return {
            "id": id,
        }

    def to_internal_value(self, value):
        if not isinstance(value, dict):
            raise ValidationError(
                self.invalid_format_error % {"data": type(value).__name__}
            )
        if "id" not in value:
            raise ValidationError(self.missing_id_error % {"data": value})

        id = value["id"]
        if not id:
            if self.required:
                raise ValidationError(self.missing_id_error % {"data": value})
            return None

        return super().to_internal_value(id)


class GeoJSONField(serializers.JSONField):
    def to_internal_value(self, data):
        if not data:
            return None
        geometry = data.get("geometry", None) or data
        gc = GeometryCollection()

        if "type" not in data:
            raise ValidationError(
                'Invalid geojson format. "type" field is required. Got %(data)s'
                % {"data": data}
            )

        supported_types = [
            "Feature",
            "Point",
            "LineString",
            "Polygon",
            "MultiPoint",
            "MultiLineString",
            "MultiPolygon",
            "FeatureCollection",
        ]
        if data["type"] not in supported_types:
            raise ValidationError(
                "Invalid geojson format. Type is not supported."
                "Supported types are %(types)s. Got %(data)s"
                % {"types": ", ".join(supported_types), "data": data}
            )

        try:
            if data.get("features"):
                for feature in data.get("features"):
                    feature_geometry = feature.get("geometry")
                    feature_geos = GEOSGeometry(json.dumps(feature_geometry))
                    gc.append(feature_geos)

            else:
                GEOSGeometry(json.dumps(geometry))

        except GDALException:
            raise ValidationError("Invalid geojson format: %(data)s" % {"data": data})

        return super(GeoJSONField, self).to_internal_value(data)


class GeometryBboxFilterBackend(BaseFilterBackend):
    """
    Filter ViewSets with a geometry field by bounding box
    """

    def filter_queryset(self, request, queryset, view):
        srs = srid_to_srs(request.query_params.get("srid", None))
        bbox = request.query_params.get("bbox", None)
        if bbox:
            bbox_filter = build_bbox_filter(srs, bbox, "geometry")
            queryset = queryset.filter(**bbox_filter)
        return queryset


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:image"):
            # base64 encoded image - decode
            try:
                format, imgstr = data.split(";base64,")
            except ValueError:
                raise ValidationError(_("Not a valid base64 image."))

            ext = format.split("/")[-1]  # guess file extension

            data = ContentFile(
                base64.b64decode(imgstr), name="%s.%s" % (get_random_string(8), ext)
            )

            # Do not limit image size if there is no settings for that
            if data.size <= getattr(settings, "MAX_IMAGE_SIZE", data.size):
                return super(Base64ImageField, self).to_internal_value(data)
            else:
                raise ValidationError(
                    _(
                        "Image size should be smaller than {} bytes.".format(
                            settings.MAX_IMAGE_SIZE
                        )
                    )
                )
        raise ValidationError(_('Invalid content. Expected "data:image"'))


class Base64FileField(serializers.FileField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith("data:application"):
            # base64 encoded file - decode
            try:
                format, filestr = data.split(";base64,")
            except ValueError:
                raise ValidationError(_("Not a valid base64 file."))

            ext = format.split("/")[-1]  # guess file extension

            data = ContentFile(
                base64.b64decode(filestr), name="%s.%s" % (get_random_string(8), ext)
            )

            # Do not limit file size if there is no settings for that
            if data.size <= getattr(settings, "MAX_FILE_SIZE", data.size):
                return super().to_internal_value(data)
            else:
                raise ValidationError(
                    _(
                        "File size should be smaller than {} bytes.".format(
                            settings.MAX_FILE_SIZE
                        )
                    )
                )
        raise ValidationError(_('Invalid content. Expected "data:application"'))


class TranslatableSerializer(serializers.Serializer):
    """
    A serializer for translated fields.

    translated_fields must be declared in the Meta class.
    By default, translation languages obtained from settings, but can be overriden
    by defining translation_lang in the Meta class.

    Translated fields may be provided either as JSON objects or stringified JSON objects. This means the
    serializer may be used for both JSON and multipart request formatting.
    """  # noqa: E501

    def __init__(self, *args, **kwargs):
        self.Meta.translated_fields = [
            field
            for field in self.Meta.model._parler_meta._fields_to_model
            if field in self.Meta.fields
        ]
        non_translated_fields = [
            field
            for field in self.Meta.fields
            if field not in self.Meta.translated_fields
        ]
        self.Meta.fields = non_translated_fields
        super(TranslatableSerializer, self).__init__(*args, **kwargs)
        self.Meta.fields = non_translated_fields + self.Meta.translated_fields
        if not hasattr(self.Meta, "translation_lang"):
            self.Meta.translation_lang = [
                lang["code"] for lang in settings.PARLER_LANGUAGES[None]
            ]

    def _update_lang(self, ret, field, value, lang_code):
        if not ret.get(field) or isinstance(ret[field], str):
            ret[field] = {}
        if value:
            ret[field][lang_code] = value
        return ret

    def to_representation(self, instance):
        ret = super(TranslatableSerializer, self).to_representation(instance)
        # enforce consistent order of translations in the API
        if "translations" in (
            cache := getattr(instance, "_prefetched_objects_cache", {})
        ):
            translations = [translation for translation in cache["translations"]]
            translations.sort(key=attrgetter("language_code"))

        else:
            translations = instance.translations.filter(
                language_code__in=self.Meta.translation_lang
            ).order_by("language_code")

        for translation in translations:
            for field in self.Meta.translated_fields:
                self._update_lang(
                    ret, field, getattr(translation, field), translation.language_code
                )
        return ret

    def _validate_translated_field(self, field, data):
        assert field in self.Meta.translated_fields, (
            "%s is not a translated field" % field
        )
        if data is None:
            return
        if not isinstance(data, dict):
            raise ValidationError(
                _(
                    'Not a valid translation format. Expecting {"lang_code": %(data)s}'
                    % {"data": data}
                )
            )
        for lang in data:
            if lang not in self.Meta.translation_lang:
                raise ValidationError(
                    _(
                        "%(lang)s is not a supported languages (%(allowed)s)"
                        % {
                            "lang": lang,
                            "allowed": self.Meta.translation_lang,
                        }
                    )
                )

    def validate(self, data):
        """
        Add a custom validation for translated fields.
        """
        validated_data = super().validate(data)
        errors = OrderedDict()
        for field in self.Meta.translated_fields:
            try:
                self._validate_translated_field(field, data.get(field, None))
            except ValidationError as e:
                errors[field] = e.detail

        if errors:
            raise ValidationError(errors)

        return validated_data

    def to_internal_value(self, value):
        """
        Add a custom deserialization for translated fields.
        """
        ret = super(TranslatableSerializer, self).to_internal_value(value)
        errors = {}
        for field in self.Meta.translated_fields:
            v = value.get(field)
            if v:
                if isinstance(v, str):
                    # we support stringified JSON
                    try:
                        ret[field] = json.loads(v)
                    except json.decoder.JSONDecodeError:
                        errors[field] = _(
                            'Not a valid translation format. Expecting {"lang_code": %(data)s}'  # noqa: E501
                            % {"data": v}
                        )
                elif isinstance(v, dict):
                    # as well as JSON objects
                    ret[field] = v
                else:
                    errors[field] = _(
                        'Not a valid translation format. Expecting {"lang_code": %(data)s}'  # noqa: E501
                        % {"data": v}
                    )

        if errors:
            # can't raise ValidationError here
            raise ParseError(errors)

        return ret

    def save(self, **kwargs):
        """
        Extract the translations and save them after main object save.
        """
        translated_data = self._pop_translated_data()
        if not self.instance:
            # forces the translation to be created, since the object cannot be saved
            # without
            self.validated_data[self.Meta.translated_fields[0]] = ""
        instance = super(TranslatableSerializer, self).save(**kwargs)
        self.save_translations(instance, translated_data)
        instance.save()
        return instance

    def _pop_translated_data(self):
        """
        Separate data of translated fields from other data.
        """
        translated_data = {}
        for meta in self.Meta.translated_fields:
            translations = self.validated_data.pop(meta, {})
            if translations:
                translated_data[meta] = translations
        return translated_data

    def save_translations(self, instance, translated_data):
        """
        Save translation data into translation objects.
        """
        for field in self.Meta.translated_fields:
            translations = {}
            if not self.partial:
                translations = {
                    lang_code: "" for lang_code in self.Meta.translation_lang
                }
            translations.update(translated_data.get(field, {}))

            for lang_code, value in translations.items():
                translation = instance._get_translated_model(
                    lang_code, auto_create=True
                )
                setattr(translation, field, value)
        instance.save_translations()
