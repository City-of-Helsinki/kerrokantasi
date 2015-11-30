import logging
import random
from datetime import timedelta

import factory
import factory.fuzzy
from django.utils.timezone import now

from kk.enums import Commenting, SectionType
from kk.factories.comment import BaseCommentFactory
from kk.models import Hearing, HearingComment, Label, Section, SectionComment

LOG = logging.getLogger(__name__)


class LabelFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Label

    label = factory.Faker("sentence")


class HearingCommentFactory(BaseCommentFactory):

    class Meta:
        model = HearingComment


class SectionCommentFactory(BaseCommentFactory):

    class Meta:
        model = SectionComment


class HearingFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Hearing

    close_at = factory.LazyAttribute(lambda obj: factory.fuzzy.FuzzyDateTime(
        start_dt=now() + timedelta(days=5),
        end_dt=now() + timedelta(days=150),
    ).fuzz())
    title = factory.Faker("sentence")
    abstract = factory.Faker("text")
    borough = factory.Faker("city")
    commenting = factory.fuzzy.FuzzyChoice(choices=Commenting)

    @factory.post_generation
    def post(obj, create, extracted, **kwargs):
        for x in range(random.randint(0, 3)):
            label = Label.objects.order_by("?").first()
            if label:  # pragma: no branch
                obj.labels.add(label)

        for x in range(random.randint(1, 5)):
            section = SectionFactory(hearing=obj)
            LOG.info("Hearing %s: Created section %s", obj, section)

        for x in range(random.randint(1, 5)):
            comment = HearingCommentFactory(hearing=obj)
            LOG.info("Hearing %s: Created comment %s", obj, comment)

        obj.recache_n_comments()


class SectionFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Section

    title = factory.Faker("sentence")
    abstract = factory.Faker("paragraph")
    content = factory.Faker("text")
    type = factory.fuzzy.FuzzyChoice(choices=SectionType)
    commenting = factory.fuzzy.FuzzyChoice(choices=Commenting)

    @factory.post_generation
    def post(obj, create, extracted, **kwargs):
        for x in range(random.randint(1, 5)):
            comment = SectionCommentFactory(section=obj)
            LOG.info("Hearing %s: Section %s: Created section comment %s", obj.hearing, obj, comment.pk)
        obj.recache_n_comments()
