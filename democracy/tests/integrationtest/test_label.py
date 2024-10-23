import pytest
from django.urls import reverse

from audit_log.enums import Operation
from democracy.models import Label
from democracy.tests.conftest import default_lang_code
from democracy.tests.utils import assert_audit_log_entry, get_data_from_response


@pytest.fixture
def valid_label_json(default_label):
    return {
        "label": {default_lang_code: default_label.label},
    }


def test_label_str():
    assert str(Label(label="label")) == "label"


@pytest.mark.django_db
def test_get_label_list_check_fields(api_client, random_label):
    data = get_data_from_response(api_client.get(reverse("label-list")))
    assert len(data["results"]) == 1

    label_data = data["results"][0]
    assert set(label_data.keys()) == {"id", "label"}
    assert label_data["label"][default_lang_code] == random_label.label


@pytest.mark.django_db
def test_cannot_post_label_without_authentication(api_client, valid_label_json):
    response = api_client.post(
        reverse("label-list"), data=valid_label_json, format="json"
    )
    data = get_data_from_response(response, status_code=401)
    assert data == {"detail": "Authentication credentials were not provided."}


@pytest.mark.django_db
def test_cannot_post_label_without_authorization(john_doe_api_client, valid_label_json):
    response = john_doe_api_client.post(
        reverse("label-list"), data=valid_label_json, format="json"
    )
    data = get_data_from_response(response, status_code=403)
    assert data == {"status": "User without organization cannot POST labels."}


@pytest.mark.django_db
def test_admin_user_can_post_label(john_smith_api_client, valid_label_json):
    response = john_smith_api_client.post(
        reverse("label-list"), data=valid_label_json, format="json"
    )
    data = get_data_from_response(response, status_code=201)
    assert data["label"] == valid_label_json["label"]


@pytest.mark.django_db
def test_label_id_is_audit_logged_on_retrieve(
    api_client, random_label, audit_log_configure
):
    url = reverse("label-detail", kwargs={"pk": random_label.pk})

    response = api_client.get(url)
    data = get_data_from_response(response)

    assert_audit_log_entry(url, [data["id"]], operation=Operation.READ)


@pytest.mark.django_db
def test_label_ids_are_audit_logged_on_list(
    api_client, random_label, audit_log_configure
):
    url = reverse("label-list")

    response = api_client.get(url)
    data = get_data_from_response(response)

    assert_audit_log_entry(url, [data["results"][0]["id"]], operation=Operation.READ)


@pytest.mark.django_db
def test_label_id_is_audit_logged_on_create(
    api_client, john_smith_api_client, valid_label_json, audit_log_configure
):
    url = reverse("label-list")
    response = john_smith_api_client.post(url, data=valid_label_json, format="json")
    data = get_data_from_response(response, status_code=201)

    assert_audit_log_entry(url, [data["id"]], operation=Operation.CREATE)
