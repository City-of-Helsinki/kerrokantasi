import pytest


def test_healthz(client):
    response = client.get("/healthz")
    assert response.status_code == 200


@pytest.mark.django_db
def test_readiness(client):
    response = client.get("/readiness")
    assert response.status_code == 200
