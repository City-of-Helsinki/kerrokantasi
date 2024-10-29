import pytest
from django.urls import reverse

from audit_log.enums import Operation
from democracy.tests.utils import assert_audit_log_entry


def get_hearing_follow_url(hearing_id):
    # /v1/hearings/<hearingID>/follow/
    return reverse("hearing-follow", kwargs={"pk": hearing_id})


def get_hearing_unfollow_url(hearing_id):
    # /v1/hearings/<hearingID>/unfollow/
    return reverse("hearing-unfollow", kwargs={"pk": hearing_id})


@pytest.mark.django_db
def test_10_hearing_follow_without_authentication(api_client, default_hearing):
    response = api_client.post(get_hearing_follow_url(default_hearing.id))
    assert response.status_code == 401


@pytest.mark.django_db
def test_10_hearing_follow(john_doe_api_client, default_hearing):
    response = john_doe_api_client.post(get_hearing_follow_url(default_hearing.id))
    assert response.status_code == 201
    assert john_doe_api_client.user.followed_hearings.filter(
        pk=default_hearing.id
    ).exists()


@pytest.mark.django_db
def test_10_hearing_follow_again(john_doe_api_client, default_hearing):
    response = john_doe_api_client.post(get_hearing_follow_url(default_hearing.id))
    assert response.status_code == 201
    response = john_doe_api_client.post(get_hearing_follow_url(default_hearing.id))
    assert response.status_code == 304


@pytest.mark.django_db
def test_hearing_unfollow(api_client, john_doe_api_client, default_hearing):
    response = api_client.post(get_hearing_unfollow_url(default_hearing.id))
    assert response.status_code == 401
    response = john_doe_api_client.post(get_hearing_follow_url(default_hearing.id))
    assert response.status_code == 201
    response = john_doe_api_client.post(get_hearing_unfollow_url(default_hearing.id))
    assert response.status_code == 204
    response = john_doe_api_client.post(get_hearing_unfollow_url(default_hearing.id))
    assert response.status_code == 304


@pytest.mark.django_db
def test_followed_hearing_appear_in_user_data(john_doe_api_client, default_hearing):
    john_doe_api_client.post(get_hearing_follow_url(default_hearing.id))
    response = john_doe_api_client.get(reverse("users-list"))
    assert default_hearing.id in response.data[0]["followed_hearings"]


@pytest.mark.django_db
def test_hearing_id_is_audit_logged_on_follow(
    john_doe_api_client, default_hearing, audit_log_configure
):
    url = get_hearing_follow_url(default_hearing.pk)

    john_doe_api_client.post(url)

    assert_audit_log_entry(url, [default_hearing.pk], operation=Operation.CREATE)


@pytest.mark.django_db
def test_hearing_id_is_audit_logged_on_unfollow(
    john_doe_api_client, default_hearing, audit_log_configure
):
    url = get_hearing_unfollow_url(default_hearing.pk)
    default_hearing.followers.add(john_doe_api_client.user)

    john_doe_api_client.post(url)

    assert_audit_log_entry(url, [default_hearing.pk], operation=Operation.CREATE)
