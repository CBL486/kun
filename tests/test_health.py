from fastapi.testclient import TestClient

from app.main import APP_VERSION, app


client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "ai-world",
        "version": APP_VERSION,
    }
