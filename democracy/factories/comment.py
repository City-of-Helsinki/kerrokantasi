import random

import factory
import factory.fuzzy

from democracy.factories.utils import get_random_user


class BaseCommentFactory(factory.django.DjangoModelFactory):
    created_by = factory.LazyAttribute(lambda obj: get_random_user())
    content = factory.Faker("text")

    @factory.post_generation
    def create_random_voters(self, create, create_random_voters, **kwargs):
        if not create_random_voters:
            return

        for _x in range(int(random.random() * random.random() * 5)):
            self.voters.add(get_random_user())
        self.recache_n_votes()
