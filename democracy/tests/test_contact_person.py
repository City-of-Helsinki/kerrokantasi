# -*- coding: utf-8 -*-
import pytest

from democracy.tests.utils import assert_common_keys_equal, get_data_from_response


@pytest.mark.django_db
def test_get_contact_person_list_check_fields(api_client, contact_person):
    data = get_data_from_response(api_client.get('/v1/contact_person/'))
    assert len(data['results']) == 1

    contact_person_data = data['results'][0]
    assert set(contact_person_data.keys()) == {'id', 'title', 'phone', 'email', 'name', 'organization'}
    assert_common_keys_equal(contact_person_data, {
        'name': 'John Contact',
        'title': 'Chief',
        'phone': '555-555',
        'email': 'john@contact.eu',
        'organization': 'The department for squirrel welfare',
    })
