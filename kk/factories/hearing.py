# -*- coding: utf-8 -*-
import string
from datetime import timedelta

import factory
import factory.fuzzy
import random
from django.utils.timezone import now
from kk.models import Hearing, Label, Scenario


class LabelFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Label

    label = factory.Faker("text")


class HearingFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Hearing

    # XXX: The datetimes are import-time relative :(
    close_at = factory.fuzzy.FuzzyDateTime(
        start_dt=now() + timedelta(days=5),
        end_dt=now() + timedelta(days=150),
    )
    heading = factory.fuzzy.FuzzyText(length=20, chars=(string.ascii_letters + "   "))
    abstract = factory.Faker("text")
    borough = factory.Faker("city")
    comment_option = factory.fuzzy.FuzzyChoice(choices=Hearing.COMMENT_OPTION)

    @factory.post_generation
    def post(obj, create, extracted, **kwargs):
        for x in range(random.randint(0, 3)):
            label = Label.objects.order_by("?").first()
            if label:
                obj.labels.add(label)


class ScenarioFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Scenario

    title = factory.fuzzy.FuzzyText(length=random.randint(10, 50), chars=(string.ascii_letters + "   "))
    abstract = factory.Faker("text")
    content = factory.Faker("text")

    @factory.post_generation
    def post(obj, create, extracted, **kwargs):
        hearing = Hearing.objects.order_by("?").first()
        obj.hearing = hearing
        obj.save()