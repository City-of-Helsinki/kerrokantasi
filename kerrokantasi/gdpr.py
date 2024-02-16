import threading
from django.contrib.auth import get_user_model
from helsinki_gdpr.types import ErrorResponse
from typing import Optional

from democracy.models import SectionComment

_thread_locals = threading.local()


def get_user(user: get_user_model()) -> get_user_model():
    """
    Function used by the Helsinki Profile GDPR API to get the "user" instance from the "GDPR Model"
    instance. Since in our case the GDPR Model and the user are one and the same, we simply return
    the same User instance that is given as a parameter.

    :param user: the User instance whose GDPR data is being queried
    :return: the same User instance
    """
    return user


def delete_data(user: get_user_model(), dry_run: bool) -> Optional[ErrorResponse]:
    """
    Function used by the Helsinki Profile GDPR API to delete all GDPR data collected of the user.
    The GDPR API package will run this within a transaction.

    :param  user: the User instance to be deleted along with related GDPR data
    :param dry_run: a boolean telling if this is a dry run of the function or not
    """

    user.nickname = ""
    user.first_name = ""
    user.last_name = ""
    user.email = ""
    user.is_active = False
    user.username = f"deleted-{user.id}"
    user.set_unusable_password()
    user.save()
    SectionComment.objects.filter(created_by=user).update(author_name=None)

    return None


class CurrentRequestMiddleware:
    """
    Middleware to store the current request in a thread_locals.

    In the GDPR API user data fetch the files (images & files) need to contain the absolute URL to the file.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.request = request

        try:
            response = self.get_response(request)
        except Exception:
            _thread_locals.request = None
            raise

        _thread_locals.request = None

        return response
