from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from app.local_state import LocalWorldStore
from app.main import create_app
from app.persona import PersonaStore
from app.setup import DeepSeekSetupStore, DeepSeekValidator, SetupError

TEST_KEY = "sk-test-r3-secret-ABCD"


async def ready_true() -> bool:
    return True


class FakeValidator:
    def __init__(self, error: SetupError | None = None):
        self.error = error
        self.keys: list[str] = []

    def validate(self, api_key: str) -> None:
        self.keys.append(api_key)
        if self.error:
            raise self.error


class FakeResponse:
    def __init__(self, status_code: int, payload=None, json_error=None):
        self.status_code = status_code
        self.payload = payload
        self.json_error = json_error

    def json(self):
        if self.json_error:
            raise self.json_error
        return self.payload


class FakeClient:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        if self.error:
            raise self.error
        return self.response


def make_store(tmp_path: Path, **kwargs) -> DeepSeekSetupStore:
    return DeepSeekSetupStore(tmp_path / "setup", secure_acl=False, **kwargs)


def make_client(
    setup_store: DeepSeekSetupStore,
    validator: FakeValidator,
) -> TestClient:
    return TestClient(
        create_app(
            store=LocalWorldStore(),
            readiness_check=ready_true,
            setup_store=setup_store,
            setup_validator=validator,
            persona_store=PersonaStore(setup_store.root.parent / "persona"),
            setup_gate=True,
        )
    )


def test_setup_store_persists_private_key_and_mask(tmp_path) -> None:
    store = make_store(tmp_path)
    validator = FakeValidator()

    first = store.save_key(TEST_KEY, validator)
    reloaded = make_store(tmp_path).status()
    completed = store.complete(persona_configured=True)

    assert validator.keys == [TEST_KEY]
    assert first.configured is True
    assert first.key_hint == "sk-...ABCD"
    assert reloaded.configured is True
    assert reloaded.key_hint == "sk-...ABCD"
    assert completed.world_ready is True
    assert completed.persona_configured is True
    assert store.key_path.read_text(encoding="utf-8").strip() == TEST_KEY
    state = json.loads(store.state_path.read_text(encoding="utf-8"))
    assert TEST_KEY not in json.dumps(state)


def test_setup_api_requires_key_before_completion(tmp_path) -> None:
    store = make_store(tmp_path)
    client = make_client(store, FakeValidator())
    try:
        status = client.get("/api/setup/status").json()
        assert status == {
            "configured": False,
            "provider": "deepseek",
            "key_hint": None,
            "persona_configured": False,
            "world_ready": False,
        }
        response = client.post("/api/setup/complete", json={})
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "deepseek_not_configured"
    finally:
        client.close()


def test_setup_gate_blocks_public_projection_routes(tmp_path) -> None:
    client = make_client(make_store(tmp_path), FakeValidator())
    try:
        for path in ("/world", "/agent", "/timeline"):
            response = client.get(path)
            assert response.status_code == 409
            assert response.json()["error"]["code"] == "setup_required"
        response = client.post(
            "/chat",
            json={"message": "未配置时不能访问"},
        )
        assert response.status_code == 409
        assert response.json()["error"]["code"] == "setup_required"
    finally:
        client.close()


def test_setup_flow_gates_root_without_echoing_key(tmp_path) -> None:
    store = make_store(tmp_path)
    validator = FakeValidator()
    client = make_client(store, validator)
    try:
        setup_page = client.get("/")
        assert setup_page.status_code == 200
        assert "DeepSeek API Key" in setup_page.text
        assert "青禾镇观察站" not in setup_page.text

        validated = client.post(
            "/api/setup/deepseek/validate",
            json={"api_key": TEST_KEY},
        )
        assert validated.status_code == 200
        assert validated.json() == {"valid": True, "provider": "deepseek"}
        assert TEST_KEY not in validated.text

        saved = client.post(
            "/api/setup/deepseek/save",
            json={"api_key": TEST_KEY},
        )
        assert saved.status_code == 200
        assert saved.json()["key_hint"] == "sk-...ABCD"
        assert TEST_KEY not in saved.text

        completed = client.post(
            "/api/setup/complete",
            json={},
        )
        assert completed.status_code == 409
        assert completed.json()["error"]["code"] == "persona_not_configured"

        persona = client.post("/api/persona/default", json={})
        assert persona.status_code == 200
        completed = client.post(
            "/api/setup/complete",
            json={},
        )
        assert completed.status_code == 200
        assert completed.json()["world_ready"] is True
        world_page = client.get("/")
        assert "青禾镇观察站" in world_page.text

        cleared = client.post("/api/setup/deepseek/clear", json={})
        assert cleared.status_code == 200
        assert cleared.json()["configured"] is False
        assert cleared.json()["persona_configured"] is True
        assert "DeepSeek API Key" in client.get("/").text
    finally:
        client.close()


def test_setup_errors_do_not_echo_secret(tmp_path) -> None:
    error = SetupError(
        "deepseek_auth_failed",
        "DeepSeek Key 无效或没有权限",
        status_code=422,
    )
    client = make_client(make_store(tmp_path), FakeValidator(error))
    try:
        response = client.post(
            "/api/setup/deepseek/save",
            json={"api_key": TEST_KEY},
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "deepseek_auth_failed"
        assert TEST_KEY not in response.text
    finally:
        client.close()


@pytest.mark.parametrize(
    ("response", "error", "code"),
    [
        (
            FakeResponse(401, {}),
            None,
            "deepseek_auth_failed",
        ),
        (
            FakeResponse(429, {}),
            None,
            "deepseek_quota_unavailable",
        ),
        (
            None,
            httpx.TimeoutException("timeout"),
            "deepseek_timeout",
        ),
        (
            None,
            httpx.ConnectError("offline"),
            "deepseek_network_error",
        ),
        (
            FakeResponse(200, {"unexpected": True}),
            None,
            "deepseek_invalid_response",
        ),
    ],
)
def test_deepseek_validator_maps_failures(response, error, code) -> None:
    validator = DeepSeekValidator(
        client=FakeClient(response=response, error=error),
    )
    with pytest.raises(SetupError) as caught:
        validator.validate(TEST_KEY)
    assert caught.value.code == code


def test_setup_lock_busy_is_typed(tmp_path) -> None:
    store = make_store(tmp_path, lock_timeout_seconds=0.1)
    lock_path = store.root / ".setup.lock"
    lock_path.write_text("busy", encoding="utf-8")
    try:
        with pytest.raises(SetupError) as caught:
            store.complete(persona_configured=True)
        assert caught.value.code == "setup_lock_busy"
    finally:
        lock_path.unlink(missing_ok=True)


def test_setup_frontend_never_uses_browser_credential_storage() -> None:
    html = Path("web/setup.html").read_text(encoding="utf-8")
    javascript = Path("web/setup.js").read_text(encoding="utf-8")
    combined = html + javascript
    assert "localStorage" not in combined
    assert "sessionStorage" not in combined
    assert "document.cookie" not in combined
    assert "AIWORLD_LLM_API_KEY" not in combined
    assert "sk-test-r3-secret" not in combined
    assert 'autocomplete="off"' in html
    assert "type=\"password\"" in html
    assert "DeepSeek Key" in javascript


@pytest.mark.skipif(os.name != "nt", reason="Windows ACL integration test")
def test_setup_acl_uses_sids_on_real_windows(tmp_path) -> None:
    store = DeepSeekSetupStore(tmp_path / "private", secure_acl=True)
    status = store.save_key(TEST_KEY, FakeValidator())
    assert status.configured is True
    result = subprocess.run(
        ["icacls", str(store.root)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "*S-1-5-32-544" in result.stdout or "BUILTIN\\Administrators" in result.stdout
    assert "*S-1-5-18" in result.stdout or "NT AUTHORITY\\SYSTEM" in result.stdout
