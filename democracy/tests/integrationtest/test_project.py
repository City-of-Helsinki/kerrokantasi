import pytest
from django.urls import reverse

from democracy.factories.hearing import HearingFactory
from democracy.models import Project, ProjectPhase
from democracy.tests.utils import get_data_from_response


def create_project():
    project_data = {"title": "Default project", "identifier": "123456"}
    project = Project.objects.create(**project_data)
    for i in range(1, 4):
        phase_data = {
            "project": project,
            "title": "Phase %d" % i,
            "description": "Phase %d description" % i,
            "schedule": "Phase %d schedule" % i,
        }
        phase = ProjectPhase.objects.create(**phase_data)
        HearingFactory(project_phase=phase)


@pytest.mark.django_db
def test_get_projects(default_project, api_client):
    url = reverse("project-list")
    project_list = get_data_from_response(api_client.get(url))["results"]
    assert len(project_list) == 1
    assert len(project_list[0]["phases"]) == 3
    assert project_list[0]["id"] == default_project.id
    assert project_list[0]["title"]["en"] == default_project.title


@pytest.mark.django_db
def test_get_project_queries(django_assert_max_num_queries, api_client):
    for _i in range(1, 4):
        create_project()
    url = reverse("project-list")
    with django_assert_max_num_queries(7):
        api_client.get(url)
