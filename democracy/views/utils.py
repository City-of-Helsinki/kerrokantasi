# -*- coding: utf-8 -*-
import base64
from collections import OrderedDict
from functools import lru_cache
import json

from django.conf import settings
from django.contrib.gis.geos import GEOSGeometry
from django.contrib.gis.gdal.error import GDALException
from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import ContentFile
from django.db.models.query import QuerySet
from django.utils.crypto import get_random_string
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from rest_framework.relations import ManyRelatedField, MANY_RELATION_KWARGS, PrimaryKeyRelatedField


class AbstractFieldSerializer(serializers.RelatedField):
    parent_serializer_class = serializers.ModelSerializer
    many_field_class = ManyRelatedField

    def to_representation(self, image):
        return self.parent_serializer_class(image, context=self.context).data

    @classmethod
    def many_init(cls, *args, **kwargs):
        list_kwargs = {'child_relation': cls(*args, **kwargs)}
        for key in kwargs.keys():
            if key in MANY_RELATION_KWARGS:
                list_kwargs[key] = kwargs[key]
        return cls.many_field_class(**list_kwargs)


class AbstractSerializerMixin(object):

    @classmethod
    @lru_cache()
    def get_field_serializer_class(cls, many_field_class=ManyRelatedField):
        return type('%sFieldSerializer' % cls.Meta.model, (AbstractFieldSerializer,), {
            "parent_serializer_class": cls,
            "many_field_class": many_field_class,
        })

    @classmethod
    def get_field_serializer(cls, **kwargs):
        many_field_class = kwargs.pop("many_field_class", ManyRelatedField)
        return cls.get_field_serializer_class(many_field_class=many_field_class)(**kwargs)


class IOErrorIgnoringManyRelatedField(ManyRelatedField):
    """
    A ManyRelatedField that ignores IOErrors occurring during iterating the children.

    This is mainly useful for images that are referenced in the database but do not exist
    on the server (where constructing them requires accessing them to populate the width
    and height fields).
    """
    def to_representation(self, iterable):
        out = []
        if isinstance(iterable, QuerySet):
            iterable = iterable.iterator()
        while True:
            try:
                value = next(iterable)
                out.append(self.child_relation.to_representation(value))
            except StopIteration:
                break
            except IOError:
                continue
        return out


class PublicFilteredImageField(serializers.Field):

    def __init__(self, *args, **kwargs):
        self.serializer_class = kwargs.pop('serializer_class', None)
        if not self.serializer_class:
            raise ImproperlyConfigured('Keyword argument serializer_class required')
        super().__init__(*args, **kwargs)

    def to_representation(self, images):
        request = self.context.get('request')

        if request and request.user and request.user.is_authenticated() and request.user.is_superuser:
            images = images.with_unpublished()
        else:
            images = images.public()

        serializer = self.serializer_class.get_field_serializer(
            many=True, read_only=True, many_field_class=IOErrorIgnoringManyRelatedField
        )
        serializer.bind(self.source, self)  # this is needed to get context in the serializer

        return serializer.to_representation(images)


def filter_by_hearing_visible(queryset, request, hearing_lookup='hearing'):
    if hearing_lookup:
        hearing_lookup = '%s__' % hearing_lookup

    filters = {
        '%sdeleted' % hearing_lookup: False,
    }
    user = request.user

    if user.is_superuser:
        return queryset.filter(**filters)

    if user.is_authenticated():
        organization = user.get_default_organization()
        if organization:
            filters['%sorganization' % hearing_lookup] = organization
            return queryset.filter(**filters)

    filters['%spublished' % hearing_lookup] = True
    filters['%sopen_at__lte' % hearing_lookup] = now()

    return queryset.filter(**filters)


class NestedPKRelatedField(PrimaryKeyRelatedField):
    """
    Support of showing and saving of expanded nesting or just a resource ID.

    The keyword argument 'expanded' defines whether the nested object is expanded or not.
    Default serializing is expanded=false.
    """

    invalid_format_error = _('Incorrect format. Expected dictionary, received %(data)s.')
    missing_id_error = _('The primary key is missing. Expected {"id": id, ...}, received %(data)s.')

    def __init__(self, *args, **kwargs):
        self.related_serializer = kwargs.pop('serializer', None)
        self.expanded = bool(kwargs.pop('expanded', False))
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
            'id': id,
        }

    def to_internal_value(self, value):
        if not isinstance(value, dict):
            raise ValidationError(self.invalid_format_error % {'data': type(value).__name__})
        if 'id' not in value:
            raise ValidationError(self.missing_id_error % {'data': value})

        id = value['id']
        if not id:
            if self.required:
                raise ValidationError(self.missing_id_error % {'data': value})
            return None

        return super().to_internal_value(id)


class GeoJSONField(serializers.JSONField):

    def to_internal_value(self, data):
        if not data:
            return None
        if "geometry" not in data:
            raise ValidationError('Invalid geojson format. "geometry" field is required. Got %(data)s' % {'data': data})

        try:
            GEOSGeometry(json.dumps(data["geometry"]))
        except GDALException:
            raise ValidationError('Invalid geojson format: %(data)s' % {'data': data})
        return super(GeoJSONField, self).to_internal_value(data)


class Base64ImageField(serializers.ImageField):

    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            # base64 encoded image - decode
            try:
                format, imgstr = data.split(';base64,')
            except ValueError:
                raise ValidationError(_('Not a valid base64 image.'))

            ext = format.split('/')[-1]  # guess file extension

            data = ContentFile(base64.b64decode(imgstr), name='%s.%s' % (get_random_string(8), ext))

            # Do not limit image size if there is no settings for that
            if data.size <= getattr(settings, 'MAX_IMAGE_SIZE', data.size):
                return super(Base64ImageField, self).to_internal_value(data)
            else:
                raise ValidationError(_('Image size should be smaller than {} bytes.'.format(settings.MAX_IMAGE_SIZE)))
        raise ValidationError(_('Invalid content. Expected "data:image"'))


class TranslatableSerializer(serializers.Serializer):
    """
    A serializer for translated fields.

    translated_fields must be declared in the Meta class.
    By default, translation languages obtained from settings, but can be overriden
    by defining translation_lang in the Meta class.
    """

    def __init__(self, *args, **kwargs):
        assert hasattr(self.Meta, 'translated_fields'), 'Improperly configured: Need to specify translated_fields'
        non_translated_fields = [field for field in self.Meta.fields if field not in self.Meta.translated_fields]
        self.Meta.fields = non_translated_fields
        super(TranslatableSerializer, self).__init__(*args, **kwargs)
        self.Meta.fields = non_translated_fields + self.Meta.translated_fields
        if not hasattr(self.Meta, 'translation_lang'):
            self.Meta.translation_lang = [lang['code'] for lang in settings.PARLER_LANGUAGES[None]]

    def _update_lang(self, ret, field, value, lang_code):
        if not ret.get(field) or isinstance(ret[field], str):
            ret[field] = {}
        if value:
            ret[field][lang_code] = value
        return ret

    def to_representation(self, instance):
        ret = super(TranslatableSerializer, self).to_representation(instance)
        translations = instance.translations.filter(language_code__in=self.Meta.translation_lang)

        for translation in translations:
            for field in self.Meta.translated_fields:
                self._update_lang(ret, field, getattr(translation, field), translation.language_code)
        return ret

    def _validate_translated_field(self, field, data):
        assert field in self.Meta.translated_fields, '%s is not a translated field' % field
        if data is None:
            return
        if not isinstance(data, dict):
            raise ValidationError(_('Not a valid translation format. Expecting {"lang_code": %(data)s}' %
                                    {'data': data}))
        for lang in data:
            if lang not in self.Meta.translation_lang:
                raise ValidationError(_('%(lang)s is not a supported languages (%(allowed)s)' % {
                    'lang': lang,
                    'allowed': self.Meta.translation_lang,
                }))

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
        ret = super(TranslatableSerializer, self).to_internal_value(value)
        for field in self.Meta.translated_fields:
            v = value.get(field)
            if v:
                ret[field] = v
        return ret

    def save(self, **kwargs):
        """
        Extract the translations and save them after main object save.
        """
        translated_data = self._pop_translated_data()
        if not self.instance:
            # forces the translation to be created, since the object cannot be saved without
            self.validated_data[self.Meta.translated_fields[0]] = ''
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
            translations = translated_data.get(field, {})
            for lang_code, value in translations.items():
                translation = instance._get_translated_model(lang_code, auto_create=True)
                setattr(translation, field, value)
        instance.save_translations()
