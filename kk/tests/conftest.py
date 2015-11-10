from django.contrib.auth.models import User

import pytest
from kk.factories.hearing import HearingFactory, LabelFactory
from kk.models import Hearing, Scenario
from kk.tests.utils import create_default_images
from rest_framework.test import APIClient


@pytest.fixture()
def default_hearing():
    """
    Fixture for a "default" hearing with three scenarios.
    All objects will have the 3 default images attached.
    """
    hearing = Hearing.objects.create(abstract='Default test hearing One')
    create_default_images(hearing)
    for x in range(1, 4):
        scenario = Scenario.objects.create(abstract='Scenario %d abstract' % x, hearing=hearing)
        create_default_images(scenario)
    return hearing


@pytest.fixture()
def random_hearing():
    return HearingFactory()


@pytest.fixture()
def random_label():
    return LabelFactory()


@pytest.fixture()
def john_doe():
    user = User.objects.filter(username="john_doe").first()
    if not user:
        user = User.objects.create_user("john_doe", "john@example.com", password="password")
    return user


@pytest.fixture()
def john_doe_api_client(john_doe):
    api_client = APIClient()
    api_client.login(username=john_doe.username, password="password")
    return api_client


@pytest.fixture()
def admin_api_client(admin_user):
    api_client = APIClient()
    api_client.login(username=admin_user.username, password="password")
    return api_client
