
from django.contrib.auth import get_user_model

from democracy.factories.user import UserFactory


def get_random_user():
    users_qs = get_user_model().objects
    if not users_qs.count():  # Last-ditch attempt to create _some_ random users
        for x in range(10):
            UserFactory()
    return users_qs.order_by("?").first()
