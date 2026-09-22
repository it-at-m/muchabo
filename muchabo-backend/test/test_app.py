from fastapi.testclient import TestClient

from muchabo.app import app


def test_healthz() -> None:
    client = TestClient(app)

    response = client.get("/api/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
