

import pytest

from democracy.tests.utils import get_data_from_response


@pytest.mark.django_db
def test_get_projects(default_project, api_client):
    url = '/v1/project/'
    project_list = get_data_from_response(api_client.get(url))['results']
    assert len(project_list) == 1
    assert len(project_list[0]['phases']) == 3
    assert project_list[0]['id'] == default_project.id
    assert project_list[0]['title']['en'] == default_project.title


