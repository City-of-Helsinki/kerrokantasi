# -*- coding: utf-8 -*-
from datetime import timedelta

import factory
import factory.fuzzy
import random
from kk.factories.utils import get_random_user


class BaseCommentFactoryMixin(object):
    created_by = factory.LazyAttribute(lambda obj: get_random_user())
    created_at = factory.LazyAttribute(lambda obj: obj.hearing.created_at + timedelta(seconds=random.randint(120, 600)))
    content = factory.Faker("text")

    @factory.post_generation
    def post(obj, create, extracted, **kwargs):
        for x in range(int(random.random() * random.random() * 5)):
            obj.followers.add(get_random_user())
        for x in range(int(random.random() * random.random() * 5)):
            obj.voters.add(get_random_user())
        obj.recache_votes()
