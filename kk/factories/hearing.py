from datetime import timedelta

import factory
import factory.fuzzy
import random
from django.utils.timezone import now
from kk.factories.comment import BaseCommentFactoryMixin
from kk.models import Hearing, Label, Scenario, HearingComment, ScenarioComment


class LabelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Label

    label = factory.Faker("sentence")


class HearingCommentFactory(BaseCommentFactoryMixin, factory.django.DjangoModelFactory):
    class Meta:
        model = HearingComment


class ScenarioCommentFactory(BaseCommentFactoryMixin, factory.django.DjangoModelFactory):
    class Meta:
        model = ScenarioComment


class HearingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Hearing

    close_at = factory.LazyAttribute(lambda obj: factory.fuzzy.FuzzyDateTime(
        start_dt=now() + timedelta(days=5),
        end_dt=now() + timedelta(days=150),
    ).fuzz())
    heading = factory.Faker("sentence")
    abstract = factory.Faker("text")
    borough = factory.Faker("city")
    comment_option = factory.fuzzy.FuzzyChoice(choices=Hearing.COMMENT_OPTION)

    @factory.post_generation
    def post(obj, create, extracted, **kwargs):
        for x in range(random.randint(0, 3)):
            label = Label.objects.order_by("?").first()
            if label:
                obj.labels.add(label)
        for x in range(random.randint(1, 5)):
            scenario = ScenarioFactory(hearing=obj)
            print(".. Created scenario %s" % scenario.pk)

        for x in range(random.randint(1, 5)):
            comment = HearingCommentFactory(hearing=obj)
            print(".. Created hearing comment %s" % comment.pk)

        obj.recache_n_comments()


class ScenarioFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Scenario

    title = factory.Faker("sentence")
    abstract = factory.Faker("paragraph")
    content = factory.Faker("text")

    @factory.post_generation
    def post(obj, create, extracted, **kwargs):
        for x in range(random.randint(1, 5)):
            comment = ScenarioCommentFactory(scenario=obj)
            print(".... Created scenario comment %s" % comment.pk)
