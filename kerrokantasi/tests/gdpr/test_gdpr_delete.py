import urllib.parse

import pytest
import requests_mock
from django.conf import settings
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from kerrokantasi.tests.gdpr.conftest import get_api_token_for_user_with_scopes

User = get_user_model()


def do_delete(
    user,
    id_value,
    scopes=(settings.GDPR_API_DELETE_SCOPE,),
    query_params=None,
    data=None,
):
    api_client = APIClient()

    with requests_mock.Mocker() as req_mock:
        auth_header = get_api_token_for_user_with_scopes(user, scopes, req_mock)
        api_client.credentials(HTTP_AUTHORIZATION=auth_header)

        if query_params:
            query = "?" + urllib.parse.urlencode(query_params)
        else:
            query = ""

        request_kwargs = {"format": "json"}
        if data:
            request_kwargs["data"] = data

        return api_client.delete(
            reverse(
                "helsinki_gdpr:gdpr_v1",
                kwargs={settings.GDPR_API_MODEL_LOOKUP: id_value},
            )
            + query,
            **request_kwargs,
        )


def assert_delete(user, original_password, client):
    user.refresh_from_db()
    assert user.username == f"deleted-{user.id}"
    assert original_password != user.password
    assert user.email == ""
    assert user.first_name == ""
    assert user.last_name == ""
    assert not user.is_active
    url = reverse("comment-list")
    response = client.get(url)
    results = response.data["results"]
    assert len(results) == 1
    assert results[0]["author_name"] is None


def delete_user(user, params):
    assert User.objects.count() == 1
    response = do_delete(user, user.uuid, **params)
    assert response.status_code == 204
    assert User.objects.count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["data", "query_params"])
def test_delete_profile_dry_run(true_value, single_comment_user, key):
    user = single_comment_user
    email = user.email
    assert email != ""
    delete_user(single_comment_user, {key: {"dry_run": true_value}})
    user.refresh_from_db()
    assert user.email == email
    assert User.objects.count() == 1


@pytest.mark.django_db
@pytest.mark.parametrize("key", ["data", "query_params"])
def test_delete_profile(api_client, false_value, single_comment_user, key):
    password = single_comment_user.password
    delete_user(single_comment_user, {key: {"dry_run": false_value}})
    assert_delete(single_comment_user, password, api_client)


@pytest.mark.django_db
def test_delete_profile_no_params(api_client, single_comment_user):
    password = single_comment_user.password
    delete_user(single_comment_user, {})
    assert_delete(single_comment_user, password, api_client)
