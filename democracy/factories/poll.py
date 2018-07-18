
import factory

from democracy.factories.hearing import SectionFactory
from democracy.models import SectionPoll, SectionPollOption


class SectionPollFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SectionPoll
        exclude = ('option_count',)

    option_count = 3
    section = factory.SubFactory(SectionFactory)
    text = factory.Faker('sentence')
    type = SectionPoll.TYPE_SINGLE_CHOICE
    is_independent_poll = False

    @factory.post_generation
    def generate_options(obj, create, extracted, **kwargs):
        option_count = kwargs.pop('option_count', 3)
        for x in range(option_count):
            SectionPollOptionFactory(poll=obj)


class SectionPollOptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SectionPollOption

    poll = factory.SubFactory(SectionPollFactory)
    text = factory.Faker('sentence')
