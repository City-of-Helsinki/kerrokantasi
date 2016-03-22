# -*- coding: utf-8 -*-
from functools import lru_cache

from django.db.models.query import QuerySet
from rest_framework import serializers
from rest_framework.relations import ManyRelatedField, MANY_RELATION_KWARGS


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
