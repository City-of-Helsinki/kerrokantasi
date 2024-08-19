import factory
from django.contrib.auth import get_user_model


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    uuid = factory.Faker("uuid4", cast_to=None)
    first_name = factory.Faker("first_name", locale="fi")
    last_name = factory.Faker("last_name")
    email = factory.Faker("email")
