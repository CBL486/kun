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
    assert response.json() == {"detail": "database unavailable"}
