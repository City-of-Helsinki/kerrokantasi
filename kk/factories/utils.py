# -*- coding: utf-8 -*-

from django.contrib.auth import get_user_model


def get_random_user():
    return get_user_model().objects.order_by("?").first()
