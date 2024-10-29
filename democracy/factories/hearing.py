import logging
import os
import random
from datetime import timedelta

import factory
import factory.fuzzy
from django.utils.timezone import now

from democracy.enums import Commenting
from democracy.factories.comment import BaseCommentFactory
from democracy.models import Hearing, Label, Section, SectionComment, SectionType
from democracy.models.section import CommentImage, SectionFile, SectionImage
from democracy.tests.utils import FILE_SOURCE_PATH, FILES

logger = logging.getLogger(__name__)


class LabelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Label

    label = factory.Faker("sentence")


class SectionCommentFactory(BaseCommentFactory):
    class Meta:
        model = SectionComment


class CommentImageFactory(factory.django.DjangoModelFactory):
    title = factory.Faker("word")
    caption = factory.Faker("word")
    image = factory.django.ImageField()

    class Meta:
        model = CommentImage


class MinimalHearingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Hearing

    title = factory.Faker("sentence")


class HearingFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Hearing

    close_at = factory.LazyAttribute(
        lambda obj: factory.fuzzy.FuzzyDateTime(
            start_dt=now() + timedelta(days=5),
            end_dt=now() + timedelta(days=150),
        ).fuzz()
    )
    title = factory.Faker("sentence")
    borough = factory.Faker("city")

    @factory.post_generation
    def post(self, create, extracted, **kwargs):
        for _x in range(random.randint(0, 3)):
            label = Label.objects.order_by("?").first()
            if label:  # pragma: no branch
                self.labels.add(label)

        SectionFactory(hearing=self, type=SectionType.objects.get(identifier="main"))

        for _x in range(random.randint(1, 4)):
            section = SectionFactory(hearing=self)
            logger.info("Hearing %s: Created section %s", self, section)

        self.recache_n_comments()


class SectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Section

    title = factory.Faker("sentence")
    abstract = factory.Faker("paragraph")
    content = factory.Faker("text")
    type = factory.fuzzy.FuzzyChoice(
        choices=SectionType.objects.exclude(identifier="main")
    )
    commenting = factory.fuzzy.FuzzyChoice(choices=Commenting)

    @factory.post_generation
    def post(self, create, extracted, **kwargs):
        for _x in range(random.randint(1, 5)):
            comment = SectionCommentFactory(section=self)
            logger.info(
                "Hearing %s: Section %s: Created section comment %s",
                self.hearing,
                self,
                comment.pk,
            )
        self.recache_n_comments()


class SectionFileFactory(factory.django.DjangoModelFactory):
    title = factory.Faker("word")
    caption = factory.Faker("word")
    file = factory.django.FileField(
        from_path=os.path.join(FILE_SOURCE_PATH, FILES["PDF"])
    )

    class Meta:
        model = SectionFile


class SectionImageFactory(factory.django.DjangoModelFactory):
    title = factory.Faker("word")
    caption = factory.Faker("word")
    alt_text = factory.Faker("word")
    image = factory.django.ImageField()

    class Meta:
        model = SectionImage
