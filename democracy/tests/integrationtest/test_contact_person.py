import pytest
from django.urls import reverse

from audit_log.enums import Operation
from democracy.factories.organization import OrganizationFactory
from democracy.models import Organization
from democracy.tests.conftest import default_lang_code
from democracy.tests.utils import (
    assert_audit_log_entry,
    assert_common_keys_equal,
    get_data_from_response,
)

LIST_ENDPOINT = reverse("contact_person-list")


@pytest.fixture
def valid_contact_person_json():
    return {
        "name": "John Contact",
        "title": {default_lang_code: "Chief"},
        "phone": "555-555",
        "email": "john@contact.eu",
        "organization": "The department for squirrel welfare",
    }


def test_cannot_get_contact_person_list_without_authentication(api_client):
    response = api_client.get(LIST_ENDPOINT)
    data = get_data_from_response(response, status_code=401)
    assert data == {"detail": "Authentication credentials were not provided."}


@pytest.mark.django_db
def test_cannot_get_contact_person_list_without_authorization(john_doe_api_client):
    response = john_doe_api_client.get(LIST_ENDPOINT)
    data = get_data_from_response(response, status_code=403)
    assert data == {
        "detail": "User without organization cannot access contact persons."
    }


@pytest.mark.django_db
def test_admin_get_contact_person_list_check_fields(
    john_smith_api_client, contact_person, valid_contact_person_json
):
    data = get_data_from_response(john_smith_api_client.get(LIST_ENDPOINT))
    assert len(data["results"]) == 1

    contact_person_data = data["results"][0]
    assert set(contact_person_data.keys()) == {
        "id",
        "title",
        "name",
        "phone",
        "email",
        "organization",
        "external_organization",
        "additional_info",
    }
    assert_common_keys_equal(contact_person_data, valid_contact_person_json)


@pytest.mark.django_db
def test_cannot_post_contact_person_without_authentication(
    api_client, valid_contact_person_json
):
    response = api_client.post(
        LIST_ENDPOINT, data=valid_contact_person_json, format="json"
    )
    data = get_data_from_response(response, status_code=401)
    assert data == {"detail": "Authentication credentials were not provided."}


@pytest.mark.django_db
def test_cannot_post_contact_person_without_authorization(
    john_doe_api_client, valid_contact_person_json
):
    response = john_doe_api_client.post(
        LIST_ENDPOINT, data=valid_contact_person_json, format="json"
    )
    data = get_data_from_response(response, status_code=403)
    assert data == {
        "detail": "User without organization cannot access contact persons."
    }


@pytest.mark.django_db
def test_admin_user_can_post_contact_person(
    john_smith_api_client, valid_contact_person_json
):
    response = john_smith_api_client.post(
        LIST_ENDPOINT, data=valid_contact_person_json, format="json"
    )
    data = get_data_from_response(response, status_code=201)
    assert set(data.keys()) == {
        "id",
        "title",
        "name",
        "phone",
        "email",
        "organization",
        "external_organization",
        "additional_info",
    }
    assert_common_keys_equal(data, valid_contact_person_json)


@pytest.mark.django_db
def test_admin_user_can_post_contact_person_for_another_organization(
    john_smith_api_client, valid_contact_person_json
):
    org_name = "The sneaky undercover department for weasel welfare"
    OrganizationFactory.create(name=org_name)
    valid_contact_person_json["organization"] = org_name
    response = john_smith_api_client.post(
        LIST_ENDPOINT, data=valid_contact_person_json, format="json"
    )
    data = get_data_from_response(response, status_code=201)
    assert data["organization"] == org_name


@pytest.mark.django_db
def test_cannot_PUT_contact_person_without_authentication(
    api_client, contact_person, valid_contact_person_json
):
    response = api_client.put(
        reverse("contact_person-detail", kwargs={"pk": contact_person.pk}),
        data=valid_contact_person_json,
        format="json",
    )

    data = get_data_from_response(response, status_code=401)

    assert data == {"detail": "Authentication credentials were not provided."}


@pytest.mark.django_db
def test_cannot_PUT_contact_person_without_authorization(
    john_doe_api_client, contact_person, valid_contact_person_json
):
    response = john_doe_api_client.put(
        reverse("contact_person-detail", kwargs={"pk": contact_person.pk}),
        data=valid_contact_person_json,
        format="json",
    )

    data = get_data_from_response(response, status_code=403)

    assert data == {
        "detail": "User without organization cannot access contact persons."
    }


@pytest.mark.django_db
def test_admin_user_can_PUT_contact_person(
    john_smith_api_client, contact_person, valid_contact_person_json
):
    valid_contact_person_json["organization"] = "The department for squirrel welfare"
    valid_contact_person_json["name"] = "John Changed-My-Last-Name"
    response = john_smith_api_client.put(
        reverse("contact_person-detail", kwargs={"pk": contact_person.pk}),
        data=valid_contact_person_json,
        format="json",
    )
    data = get_data_from_response(response, status_code=200)
    assert set(data.keys()) == {
        "id",
        "title",
        "name",
        "phone",
        "email",
        "organization",
        "external_organization",
        "additional_info",
    }
    assert_common_keys_equal(data, valid_contact_person_json)


@pytest.mark.django_db
def test_admin_user_can_PUT_contact_person_for_another_organization(
    john_smith_api_client, contact_person, valid_contact_person_json
):
    other_organization: Organization = OrganizationFactory()
    contact_person.organization = other_organization
    contact_person.save()
    response = john_smith_api_client.put(
        reverse("contact_person-detail", kwargs={"pk": contact_person.pk}),
        data=valid_contact_person_json,
        format="json",
    )
    data = get_data_from_response(response, status_code=200)
    assert data["organization"] == valid_contact_person_json["organization"]


@pytest.mark.django_db
def test_contact_person_id_is_audit_logged_on_retrieve(
    john_smith_api_client, contact_person, audit_log_configure
):
    john_smith_api_client.get(
        reverse("contact_person-detail", kwargs={"pk": contact_person.pk})
    )

    assert_audit_log_entry(LIST_ENDPOINT, [contact_person.pk], operation=Operation.READ)


@pytest.mark.django_db
def test_contact_person_ids_are_audit_logged_on_list(
    john_smith_api_client, contact_person, audit_log_configure
):
    john_smith_api_client.get(LIST_ENDPOINT)

    assert_audit_log_entry(LIST_ENDPOINT, [contact_person.pk], operation=Operation.READ)


@pytest.mark.django_db
def test_contact_person_id_is_audit_logged_on_create(
    john_smith_api_client, valid_contact_person_json, audit_log_configure
):
    response = john_smith_api_client.post(
        LIST_ENDPOINT, data=valid_contact_person_json, format="json"
    )
    data = get_data_from_response(response, status_code=201)

    assert_audit_log_entry(LIST_ENDPOINT, [data["id"]], operation=Operation.CREATE)


@pytest.mark.django_db
def test_contact_person_id_is_audit_logged_on_update(
    john_smith_api_client,
    contact_person,
    valid_contact_person_json,
    audit_log_configure,
):
    valid_contact_person_json["organization"] = "The department for squirrel welfare"
    valid_contact_person_json["name"] = "John Changed-My-Last-Name"

    response = john_smith_api_client.put(
        reverse("contact_person-detail", kwargs={"pk": contact_person.pk}),
        data=valid_contact_person_json,
        format="json",
    )
    data = get_data_from_response(response, status_code=200)

    assert_audit_log_entry(LIST_ENDPOINT, [data["id"]], operation=Operation.UPDATE)
