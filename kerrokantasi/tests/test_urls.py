def test_healthz(client):
    response = client.get("/healthz")
    assert response.status_code == 200


def test_readiness(client):
    response = client.get("/readiness")
    assert response.status_code == 200
