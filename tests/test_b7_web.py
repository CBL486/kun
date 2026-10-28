from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.local_state import LocalWorldStore
from app.main import create_app


async def ready_true() -> bool:
    return True


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(
        create_app(
            store=LocalWorldStore(),
            readiness_check=ready_true,
        )
    )


def test_web_root_serves_observer_shell(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    html = response.text
    assert 'lang="zh-CN"' in html
    assert "青禾镇观察站" in html
    assert "观察者视角" in html
    assert 'id="main-content"' in html
    assert 'href="/static/styles.css"' in html
    assert 'src="/static/app.js"' in html


def test_required_views_and_navigation_are_present(client: TestClient) -> None:
    html = client.get("/").text
    for view in (
        "map",
        "character",
        "timeline",
        "chat",
        "diary",
        "memory",
        "settings",
    ):
        assert f'data-view-panel="{view}"' in html
        assert f'data-view="{view}"' in html
    for copy in (
        "小镇此刻",
        "角色卡",
        "已经发生的事",
        "给林澄留言",
        "日记摘要",
        "记忆摘要",
        "观察设置",
    ):
        assert copy in html


def test_loading_empty_network_and_review_states_have_interfaces(
    client: TestClient,
) -> None:
    html = client.get("/").text
    assert 'id="loading-state"' in html
    assert 'id="connection-banner"' in html
    assert 'id="retry-button"' in html
    assert 'class="chat-empty"' in html
    assert 'id="chat-status"' in html
    assert "留言未通过审核" in Path("web/app.js").read_text(encoding="utf-8")


def test_static_assets_and_placeholder_fallback_exist(client: TestClient) -> None:
    for path in (
        "/static/styles.css",
        "/static/app.js",
        "/static/assets/placeholders/town-map.svg",
        "/static/assets/placeholders/avatar.svg",
        "/static/assets/placeholders/event.svg",
    ):
        response = client.get(path)
        assert response.status_code == 200, path
        assert response.content


def test_responsive_desktop_and_mobile_layouts_are_defined() -> None:
    css = Path("web/styles.css").read_text(encoding="utf-8")
    assert "grid-template-columns: var(--sidebar)" in css
    assert "@media (max-width: 760px)" in css
    assert ".mobile-nav" in css
    assert "grid-template-columns: repeat(7, 1fr)" in css
    assert "env(safe-area-inset-bottom)" in css
    html = Path("web/index.html").read_text(encoding="utf-8")
    mobile_nav = html.split('<nav class="mobile-nav"', 1)[1].split('</nav>', 1)[0]
    assert 'data-view="settings"' in mobile_nav
    assert "@media (prefers-reduced-motion: reduce)" in css


def test_frontend_uses_only_frozen_public_api_fields() -> None:
    javascript = Path("web/app.js").read_text(encoding="utf-8")
    for endpoint in ("/world", "/agent", "/timeline", "/chat", "/memory"):
        assert endpoint in javascript
    forbidden = (
        "importance",
        "emotional_weight",
        "action_score",
        "state_version",
        "memory_slots",
        "database_url",
    )
    assert not any(field in javascript for field in forbidden)
    assert "innerHTML" not in javascript


def test_observer_loop_can_reach_world_character_chat_diary_and_memory(
    client: TestClient,
) -> None:
    world = client.get("/world")
    agent = client.get("/agent")
    chat = client.post("/chat", json={"message": "今天的校刊任务进展怎么样？"})
    memory = client.get("/memory", params={"limit": 20})

    assert world.status_code == 200
    assert agent.status_code == 200
    assert chat.status_code == 200
    assert memory.status_code == 200
    assert world.json()["world"]["name"] == "青禾镇"
    assert agent.json()["agent"]["name"] == "林澄"
    assert chat.json()["status"] == "queued"
    assert memory.json()["diary_summaries"]
    assert memory.json()["items"]


def test_b75_component_interfaces_are_reserved() -> None:
    html = Path("web/index.html").read_text(encoding="utf-8")
    css = Path("web/styles.css").read_text(encoding="utf-8")
    assert 'class="map-art"' in html
    assert 'class="portrait portrait-large"' in html
    assert 'class="nav-mark"' in html
    assert ".location-card" in css
    assert ".timeline-item" in css
    assert ".memory-card" in css
    assert "assets/placeholders" in html


def test_web_has_no_external_runtime_dependency(client: TestClient) -> None:
    html = client.get("/").text
    css = client.get("/static/styles.css").text
    javascript = client.get("/static/app.js").text
    combined = "\n".join((html, css, javascript))
    assert "cdn." not in combined
    assert "unpkg.com" not in combined
    assert "googleapis.com" not in combined
    assert "AIWORLD_LLM_API_KEY" not in combined
