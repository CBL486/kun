from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.local_state import LocalWorldStore, PublicProjectionError
from app.main import create_app


async def ready_true() -> bool:
    return True


def make_client(store: LocalWorldStore) -> TestClient:
    return TestClient(create_app(store=store, readiness_check=ready_true))


def test_agent_presence_is_authoritative_and_revisioned() -> None:
    store = LocalWorldStore()
    before = store.world()
    old_revision = before.world.state_revision

    presence = store.update_agent_presence(
        location_id="loc_classroom",
        x=812.5,
        y=338.0,
        facing="left",
        animation="walk",
        speed=72.0,
        moving=True,
        updated_at="2026-11-09T08:10:12+08:00",
    )
    after = store.world()

    assert presence.revision == old_revision + 1
    assert after.world.state_revision == old_revision + 1
    assert after.world.current_location_id == "loc_classroom"
    assert after.agent_presence is not None
    assert after.agent_presence.model_dump() == presence.model_dump()
    assert after.agent_presence.x == 812.5
    assert after.agent_presence.y == 338.0
    assert after.agent_presence.facing == "left"
    assert after.agent_presence.animation == "walk"
    assert after.agent_presence.moving is True


def test_presence_rejects_revision_regression() -> None:
    store = LocalWorldStore()
    current = store.world().world.state_revision
    with pytest.raises(PublicProjectionError) as caught:
        store.update_agent_presence(
            location_id="loc_library",
            revision=current,
        )
    assert caught.value.code == "stale_presence_revision"


def test_world_is_read_only_over_public_api() -> None:
    client = make_client(LocalWorldStore())
    try:
        response = client.post(
            "/world",
            json={
                "character_id": "char_lin_cheng",
                "x": 1,
                "y": 1,
            },
        )
        assert response.status_code == 405
    finally:
        client.close()


def test_frontend_has_no_player_control_and_uses_presence() -> None:
    html = Path("web/index.html").read_text(encoding="utf-8")
    javascript = Path("web/app.js").read_text(encoding="utf-8")
    assert "data-move" not in html
    assert "WASD" not in html
    assert "MOVE_KEYS" not in javascript
    assert 'window.addEventListener("keydown"' not in javascript
    assert 'window.addEventListener("keyup"' not in javascript
    assert "agent_presence" in javascript
    assert "state_revision" in javascript
    assert "deadzoneCamera" in javascript
    assert "translate3d" in javascript
    assert "visibilitychange" in javascript
    assert "prefers-reduced-motion" in javascript
    assert 'fetchJSON("/memory' not in javascript


def test_memory_route_is_removed_from_openapi() -> None:
    client = make_client(LocalWorldStore())
    try:
        schema = client.get("/openapi.json").json()
        assert "/memory" not in schema["paths"]
        assert "getMemory" not in {
            operation["operationId"]
            for path in schema["paths"].values()
            for method, operation in path.items()
            if method in {"get", "post"}
        }
    finally:
        client.close()
