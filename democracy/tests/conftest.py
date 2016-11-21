import datetime

import pytest
from django.contrib.auth import get_user_model
from django.utils.timezone import now
from rest_framework.test import APIClient

from democracy.enums import Commenting, InitialSectionType
from democracy.factories.hearing import HearingFactory, LabelFactory
from democracy.models import ContactPerson, Hearing, Label, Section, SectionType, Organization
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
def default_organization():
    return Organization.objects.create(name='The department for squirrel welfare')


@pytest.fixture()
def contact_person(default_organization):
    return ContactPerson.objects.create(
        name='John Contact',
        title='Chief',
        phone='555-555',
        email='john@contact.eu',
        organization=default_organization
    )


@pytest.fixture()
def default_hearing(john_doe, contact_person):
    """
    Fixture for a "default" hearing with three sections (one main, two other sections).
    All objects will have the 3 default images attached.
    All objects will allow open commenting.
    """
    hearing = Hearing.objects.create(
        title='Default test hearing One',
        open_at=now() - datetime.timedelta(days=1),
        close_at=now() + datetime.timedelta(days=1),
        slug='default-hearing-slug'
    )
    for x in range(1, 4):
        section_type = (InitialSectionType.MAIN if x == 1 else InitialSectionType.SCENARIO)
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

    hearing.contact_persons.add(contact_person)

    return hearing


@pytest.fixture()
def default_label():
    label = Label.objects.create(label='The Label')
    return label


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
    api_client.force_authenticate(user=john_doe)
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
    api_client.force_authenticate(user=jane_doe)
    api_client.user = jane_doe
    return api_client


@pytest.fixture()
def john_smith(default_organization):
    """
    John Smith is registered user working for an organization.
    """
    user = get_user_model().objects.filter(username="john_smith").first()
    if not user:  # pragma: no branch
        user = get_user_model().objects.create_user("john_smith", "john_smith@example.com", password="password")
        user.admin_organizations.add(default_organization)
    return user


@pytest.fixture()
def john_smith_api_client(john_smith):
    """
    John Smith is a registered user working for an organization; this is his API client.
    """
    api_client = APIClient()
    api_client.force_authenticate(user=john_smith)
    api_client.user = john_smith
    return api_client


@pytest.fixture()
def admin_api_client(admin_user):
    api_client = APIClient()
    api_client.force_authenticate(user=admin_user)
    api_client.user = admin_user
    return api_client


@pytest.fixture()
def api_client():
    return APIClient()
