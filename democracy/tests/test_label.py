import pytest

from democracy.models import Label
from democracy.tests.utils import get_data_from_response
from democracy.tests.conftest import default_lang_code

endpoint = '/v1/label/'
list_endpoint = endpoint


@pytest.fixture
def valid_label_json(default_label):
    return {"label": {default_lang_code: default_label.label}, }


def test_label_str():
    assert str(Label(label="label")) == "label"


@pytest.mark.django_db
def test_get_label_list_check_fields(api_client, random_label):
    data = get_data_from_response(api_client.get('/v1/label/'))
    assert len(data['results']) == 1

    label_data = data['results'][0]
    assert set(label_data.keys()) == {'id', 'label'}
    assert label_data['label'][default_lang_code] == random_label.label


@pytest.mark.django_db
def test_cannot_post_label_without_authentication(api_client, valid_label_json):
    response = api_client.post(list_endpoint, data=valid_label_json, format='json')
    data = get_data_from_response(response, status_code=401)
    assert data == {'detail': 'Authentication credentials were not provided.'}


@pytest.mark.django_db
def test_cannot_post_label_without_authorization(john_doe_api_client, valid_label_json):
    response = john_doe_api_client.post(list_endpoint, data=valid_label_json, format='json')
    data = get_data_from_response(response, status_code=403)
    assert data == {"status": "User without organization cannot POST labels."}


@pytest.mark.django_db
def test_admin_user_can_post_label(api_client, john_smith_api_client, valid_label_json):
    response = john_smith_api_client.post(endpoint, data=valid_label_json, format='json')
    data = get_data_from_response(response, status_code=201)
    assert data['label'] == valid_label_json['label']
