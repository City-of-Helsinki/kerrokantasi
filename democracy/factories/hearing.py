import logging
import random
from datetime import timedelta

import factory
import factory.fuzzy
from django.utils.timezone import now

from democracy.enums import Commenting
from democracy.factories.comment import BaseCommentFactory
from democracy.models import Hearing, Label, Section, SectionComment, SectionType

LOG = logging.getLogger(__name__)


class LabelFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Label

    label = factory.Faker("sentence")


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

    @factory.post_generation
    def post(obj, create, extracted, **kwargs):
        for x in range(random.randint(0, 3)):
            label = Label.objects.order_by("?").first()
            if label:  # pragma: no branch
                obj.labels.add(label)

        SectionFactory(hearing=obj, type=SectionType.objects.get(identifier='introduction'))

        for x in range(random.randint(1, 4)):
            section = SectionFactory(hearing=obj)
            LOG.info("Hearing %s: Created section %s", obj, section)

        obj.recache_n_comments()


class SectionFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Section

    title = factory.Faker("sentence")
    abstract = factory.Faker("paragraph")
    content = factory.Faker("text")
    type = factory.fuzzy.FuzzyChoice(choices=SectionType.objects.exclude(identifier='introduction'))
    commenting = factory.fuzzy.FuzzyChoice(choices=Commenting)

    @factory.post_generation
    def post(obj, create, extracted, **kwargs):
        for x in range(random.randint(1, 5)):
            comment = SectionCommentFactory(section=obj)
            LOG.info("Hearing %s: Section %s: Created section comment %s", obj.hearing, obj, comment.pk)
        obj.recache_n_comments()
