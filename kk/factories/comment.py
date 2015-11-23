# -*- coding: utf-8 -*-
import random
from datetime import timedelta

import factory
import factory.fuzzy

from kk.factories.utils import get_random_user


class BaseCommentFactory(factory.django.DjangoModelFactory):
    created_by = factory.LazyAttribute(lambda obj: get_random_user())
    content = factory.Faker("text")

    @factory.post_generation
    def post(obj, create, extracted, **kwargs):
        for x in range(int(random.random() * random.random() * 5)):
            obj.voters.add(get_random_user())
        obj.recache_n_votes()

        # Can't be done in a lazy attribute because they have no access to the concrete factory's model class,
        # for `parent_field`...
        obj.created_at = getattr(obj, obj.parent_field).created_at + timedelta(seconds=random.randint(120, 600))
        obj.save(update_fields=("created_at", ))
