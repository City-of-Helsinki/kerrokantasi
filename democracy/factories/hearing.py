import factory
import factory.fuzzy
import logging
import os
import random
from datetime import timedelta
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
    def post(obj, create, extracted, **kwargs):
        for x in range(random.randint(0, 3)):
            label = Label.objects.order_by("?").first()
            if label:  # pragma: no branch
                obj.labels.add(label)

        SectionFactory(hearing=obj, type=SectionType.objects.get(identifier="main"))

        for x in range(random.randint(1, 4)):
            section = SectionFactory(hearing=obj)
            logger.info("Hearing %s: Created section %s", obj, section)

        obj.recache_n_comments()


class SectionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Section

    title = factory.Faker("sentence")
    abstract = factory.Faker("paragraph")
    content = factory.Faker("text")
    type = factory.fuzzy.FuzzyChoice(choices=SectionType.objects.exclude(identifier="main"))
    commenting = factory.fuzzy.FuzzyChoice(choices=Commenting)

    @factory.post_generation
    def post(obj, create, extracted, **kwargs):
        for x in range(random.randint(1, 5)):
            comment = SectionCommentFactory(section=obj)
            logger.info("Hearing %s: Section %s: Created section comment %s", obj.hearing, obj, comment.pk)
        obj.recache_n_comments()


class SectionFileFactory(factory.django.DjangoModelFactory):
    title = factory.Faker("word")
    caption = factory.Faker("word")
    file = factory.django.FileField(from_path=os.path.join(FILE_SOURCE_PATH, FILES["PDF"]))

    class Meta:
        model = SectionFile


class SectionImageFactory(factory.django.DjangoModelFactory):
    title = factory.Faker("word")
    caption = factory.Faker("word")
    alt_text = factory.Faker("word")
    image = factory.django.ImageField()

    class Meta:
        model = SectionImage
