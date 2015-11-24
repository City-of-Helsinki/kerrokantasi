import pytest

from kk.tests.utils import get_hearing_detail_url


def get_hearing_follow_url(hearing_id):
    # /v1/hearings/<hearingID>/follow/
    return get_hearing_detail_url(hearing_id, 'follow')


def get_hearing_unfollow_url(hearing_id):
    # /v1/hearings/<hearingID>/unfollow/
    return get_hearing_detail_url(hearing_id, 'unfollow')


@pytest.mark.django_db
def test_10_hearing_follow_without_authentication(client, default_hearing):
    response = client.post(get_hearing_follow_url(default_hearing.id))
    assert response.status_code == 403


@pytest.mark.django_db
def test_10_hearing_follow(john_doe_api_client, default_hearing):
    response = john_doe_api_client.post(get_hearing_follow_url(default_hearing.id))
    assert response.status_code == 201
    assert john_doe_api_client.user.followed_hearings.filter(pk=default_hearing.id).exists()


@pytest.mark.django_db
def test_10_hearing_follow_again(john_doe_api_client, default_hearing):
    response = john_doe_api_client.post(get_hearing_follow_url(default_hearing.id))
    assert response.status_code == 201
    response = john_doe_api_client.post(get_hearing_follow_url(default_hearing.id))
    assert response.status_code == 304


@pytest.mark.django_db
def test_hearing_unfollow(client, john_doe_api_client, default_hearing):
    response = client.post(get_hearing_unfollow_url(default_hearing.id))
    assert response.status_code == 403
    response = john_doe_api_client.post(get_hearing_follow_url(default_hearing.id))
    assert response.status_code == 201
    response = john_doe_api_client.post(get_hearing_unfollow_url(default_hearing.id))
    assert response.status_code == 204
    response = john_doe_api_client.post(get_hearing_unfollow_url(default_hearing.id))
    assert response.status_code == 304


@pytest.mark.django_db
def test_followed_hearing_appear_in_user_data(john_doe_api_client, default_hearing):
    john_doe_api_client.post(get_hearing_follow_url(default_hearing.id))
    response = john_doe_api_client.get('/v1/users/')
    assert default_hearing.id in response.data[0]['followed_hearings']
