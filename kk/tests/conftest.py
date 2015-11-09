import pytest
from kk.factories.hearing import HearingFactory, LabelFactory
from kk.models import Hearing, Introduction, Scenario
from kk.tests.utils import create_default_images


@pytest.fixture()
def default_hearing():
    """
    Fixture for a "default" hearing with one introduction and three scenarios.
    All objects will have the 3 default images attached.
    """
    hearing = Hearing.objects.create(abstract='Default test hearing One')
    create_default_images(hearing)
    introduction = Introduction.objects.create(abstract='Introduction abstract', hearing=hearing)
    create_default_images(introduction)
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
