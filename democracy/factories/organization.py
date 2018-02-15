
import factory
import factory.fuzzy
from democracy.models import Organization


class OrganizationFactory(factory.django.DjangoModelFactory):

    class Meta:
        model = Organization

    name = factory.Faker('sentence')
