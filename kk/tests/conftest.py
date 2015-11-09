import pytest
from kk.models import Hearing, Scenario
from kk.tests.utils import create_default_images


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
