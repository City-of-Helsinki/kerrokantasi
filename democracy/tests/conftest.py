import datetime

import pytest
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from rest_framework.test import APIClient

from democracy.enums import Commenting, InitialSectionType
from democracy.factories.hearing import HearingFactory, LabelFactory
from democracy.models import Hearing, HearingComment, Label, Section, SectionType
from democracy.tests.utils import assert_ascending_sequence, create_default_images


default_comment_content = 'I agree with you sir Lancelot. My favourite colour is blue'
red_comment_content = 'Mine is red'
green_comment_content = 'I like green'


def pytest_configure():
    # During tests, crypt passwords with MD5. This should make things run faster.
    from django.conf import settings
    settings.PASSWORD_HASHERS = (
        'django.contrib.auth.hashers.MD5PasswordHasher',
        'django.contrib.auth.hashers.PBKDF2PasswordHasher',
        'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
        'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
        'django.contrib.auth.hashers.BCryptPasswordHasher',
        'django.contrib.auth.hashers.SHA1PasswordHasher',
        'django.contrib.auth.hashers.CryptPasswordHasher',
    )


@pytest.fixture()
def default_hearing(john_doe):
    """
    Fixture for a "default" hearing with three sections (one introduction, two sections).
    All objects will have the 3 default images attached.
    All objects will allow open commenting.
    """
    hearing = Hearing.objects.create(
        title='Default test hearing One',
        abstract='Default test hearing One',
        commenting=Commenting.OPEN,
        open_at=now() - datetime.timedelta(days=1),
        close_at=now() + datetime.timedelta(days=1),
        slug='default-hearing-slug'
    )
    create_default_images(hearing)
    for x in range(1, 4):
        section_type = (InitialSectionType.INTRODUCTION if x == 1 else InitialSectionType.SCENARIO)
        section = Section.objects.create(
            abstract='Section %d abstract' % x,
            hearing=hearing,
            type=SectionType.objects.get(identifier=section_type),
            commenting=Commenting.OPEN
        )
        create_default_images(section)
        section.comments.create(created_by=john_doe, content=default_comment_content[::-1])
        section.comments.create(created_by=john_doe, content=red_comment_content[::-1])
        section.comments.create(created_by=john_doe, content=green_comment_content[::-1])

    assert_ascending_sequence([s.ordering for s in hearing.sections.all()])

    HearingComment.objects.create(hearing=hearing, created_by=john_doe, content=default_comment_content)
    HearingComment.objects.create(hearing=hearing, created_by=john_doe, content=red_comment_content)
    HearingComment.objects.create(hearing=hearing, created_by=john_doe, content=green_comment_content)

    return hearing


@pytest.fixture()
def random_hearing():
    if not Label.objects.exists():
        LabelFactory()
    return HearingFactory()


@pytest.fixture()
def random_label():
    return LabelFactory()


@pytest.fixture()
def john_doe():
    """
    John Doe is your average registered user.
    """
    user = get_user_model().objects.filter(username="john_doe").first()
    if not user:  # pragma: no branch
        user = get_user_model().objects.create_user("john_doe", "john@example.com", password="password")
    return user


@pytest.fixture()
def john_doe_api_client(john_doe):
    """
    John Doe is your average registered user; this is his API client.
    """
    api_client = APIClient()
    api_client.login(username=john_doe.username, password="password")
    api_client.user = john_doe
    return api_client


@pytest.fixture()
def jane_doe():
    """
    Jane Doe is another average registered user.
    """
    user = get_user_model().objects.filter(username="jane_doe").first()
    if not user:  # pragma: no branch
        user = get_user_model().objects.create_user("jane_doe", "jane@example.com", password="password")
    return user


@pytest.fixture()
def jane_doe_api_client(jane_doe):
    """
    Jane Doe is another average registered user; this is her API client.
    """
    api_client = APIClient()
    api_client.login(username=jane_doe.username, password="password")
    api_client.user = jane_doe
    return api_client


@pytest.fixture()
def admin_api_client(admin_user):
    api_client = APIClient()
    api_client.login(username=admin_user.username, password="password")
    api_client.user = admin_user
    return api_client


@pytest.fixture()
def api_client():
    return APIClient()
