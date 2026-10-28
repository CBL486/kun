import app.main as main_module
from fastapi.testclient import TestClient


client = TestClient(main_module.app)


def test_ready_when_database_is_reachable(monkeypatch) -> None:
    async def fake_ready() -> bool:
        return True

    monkeypatch.setattr(main_module, "database_ready", fake_ready)
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "service": "ai-world"}


def test_ready_returns_503_when_database_is_unreachable(monkeypatch) -> None:
    async def fake_ready() -> bool:
        return False

    monkeypatch.setattr(main_module, "database_ready", fake_ready)
    response = client.get("/ready")

    assert response.status_code == 503
    payload = response.json()
    assert payload["schema_version"] == "rpg-error-v1"
    assert payload["error"]["code"] == "database_unavailable"
    assert payload["error"]["request_id"] == response.headers["X-Request-ID"]
