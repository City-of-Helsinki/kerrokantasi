import random
from datetime import timedelta

import factory
import factory.fuzzy

from democracy.factories.utils import get_random_user


class BaseCommentFactory(factory.django.DjangoModelFactory):
    created_by = factory.LazyAttribute(lambda obj: get_random_user())
    content = factory.Faker("text")

    @factory.post_generation
    def post(self, create, extracted, **kwargs):
        for _x in range(int(random.random() * random.random() * 5)):
            self.voters.add(get_random_user())
        self.recache_n_votes()

        # Can't be done in a lazy attribute because they have no access to the concrete factory's model class,  # noqa: E501
        # for `parent_field`...
        self.created_at = getattr(self, self.parent_field).created_at + timedelta(
            seconds=random.randint(120, 600)
        )
        self.save(update_fields=("created_at",))
