# -*- coding: utf-8 -*-
from functools import lru_cache

from rest_framework import serializers


class AbstractFieldSerializer(serializers.RelatedField):
    parent_serializer_class = serializers.ModelSerializer

    def to_representation(self, image):
        return self.parent_serializer_class(image, context=self.context).data


class AbstractSerializerMixin(object):
    @classmethod
    @lru_cache()
    def get_field_serializer_class(cls):
        return type('%sFieldSerializer' % cls.Meta.model, (AbstractFieldSerializer,), {
            "parent_serializer_class": cls
        })

    @classmethod
    def get_field_serializer(cls, **kwargs):
        return cls.get_field_serializer_class()(**kwargs)
