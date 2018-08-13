# -*- coding: utf-8 -*-
import pytest

from democracy.factories.organization import OrganizationFactory
from democracy.tests.utils import assert_common_keys_equal, get_data_from_response
from democracy.tests.conftest import default_lang_code

endpoint = '/v1/contact_person/'
list_endpoint = endpoint


@pytest.fixture
def valid_contact_person_json():
    return {
        'name': 'John Contact',
        'title': {default_lang_code: 'Chief'},
        'phone': '555-555',
        'email': 'john@contact.eu',
        'organization': 'The department for squirrel welfare',
    }


@pytest.mark.django_db
def test_get_contact_person_list_check_fields(api_client, contact_person, valid_contact_person_json):
    data = get_data_from_response(api_client.get('/v1/contact_person/'))
    assert len(data['results']) == 1

    contact_person_data = data['results'][0]
    assert set(contact_person_data.keys()) == {'id', 'title', 'phone', 'email', 'name', 'organization'}
    assert_common_keys_equal(contact_person_data, valid_contact_person_json)


@pytest.mark.django_db
def test_cannot_post_contact_person_without_authentication(api_client, valid_contact_person_json):
    response = api_client.post(list_endpoint, data=valid_contact_person_json, format='json')
    data = get_data_from_response(response, status_code=401)
    assert data == {'detail': 'Authentication credentials were not provided.'}


@pytest.mark.django_db
def test_cannot_post_contact_person_without_authorization(john_doe_api_client, valid_contact_person_json):
    response = john_doe_api_client.post(list_endpoint, data=valid_contact_person_json, format='json')
    data = get_data_from_response(response, status_code=403)
    assert data == {"status": "User without organization cannot POST contact persons."}


@pytest.mark.django_db
def test_admin_user_can_post_contact_person(john_smith_api_client, valid_contact_person_json):
    response = john_smith_api_client.post(endpoint, data=valid_contact_person_json, format='json')
    data = get_data_from_response(response, status_code=201)
    print(data)
    assert set(data.keys()) == {'id', 'title', 'phone', 'email', 'name', 'organization'}
    assert_common_keys_equal(data, valid_contact_person_json)


@pytest.mark.django_db
def test_admin_user_cannot_post_contact_person_for_another_organization(john_smith_api_client, valid_contact_person_json):
    valid_contact_person_json['organization'] = 'The sneaky undercover department for weasel welfare'
    response = john_smith_api_client.post(endpoint, data=valid_contact_person_json, format='json')
    data = get_data_from_response(response, status_code=400)
    assert data == {"organization": "Setting organization to The sneaky undercover department"
                                    " for weasel welfare is not allowed for your organization."
                                    " The organization must be left blank or set to The department"
                                    " for squirrel welfare."}


@pytest.mark.django_db
def test_cannot_PUT_contact_person_without_authentication(api_client, contact_person, valid_contact_person_json):
    response = api_client.put('%s%s/' % (endpoint, contact_person.pk), data=valid_contact_person_json, format='json')
    data = get_data_from_response(response, status_code=401)
    assert data == {'detail': 'Authentication credentials were not provided.'}


@pytest.mark.django_db
def test_cannot_PUT_contact_person_without_authorization(john_doe_api_client, contact_person, valid_contact_person_json):
    response = john_doe_api_client.put('%s%s/' % (endpoint, contact_person.pk), data=valid_contact_person_json, format='json')
    print(response.content)
    data = get_data_from_response(response, status_code=403)
    assert data == {"status": "User without organization cannot PUT contact persons."}


@pytest.mark.django_db
def test_admin_user_can_PUT_contact_person(john_smith_api_client, contact_person, valid_contact_person_json):
    valid_contact_person_json['organization'] = 'The department for squirrel welfare'
    valid_contact_person_json['name'] = 'John Changed-My-Last-Name'
    response = john_smith_api_client.put('%s%s/' % (endpoint, contact_person.pk), data=valid_contact_person_json, format='json')
    print(response.content)
    data = get_data_from_response(response, status_code=200)
    assert set(data.keys()) == {'id', 'title', 'phone', 'email', 'name', 'organization'}
    assert_common_keys_equal(data, valid_contact_person_json)


@pytest.mark.django_db
def test_admin_user_cannot_PUT_contact_person_for_another_organization(john_smith_api_client, contact_person, valid_contact_person_json):
    other_organization = OrganizationFactory()
    contact_person.organization = other_organization
    contact_person.save()
    response = john_smith_api_client.put('%s%s/' % (endpoint, contact_person.pk), data=valid_contact_person_json, format='json')
    print(response.content)
    data = get_data_from_response(response, status_code=403)
    assert data == {'detail': "Only organization admins can update organization contact persons."}
