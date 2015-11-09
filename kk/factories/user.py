# -*- coding: utf-8 -*-
import factory
import factory.fuzzy
from django.contrib.auth import get_user_model


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()  # XXX: This makes this file not safe to import before `django.setup()`

    username = factory.fuzzy.FuzzyText()
    first_name = factory.Faker("first_name", locale="fi")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
