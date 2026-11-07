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
        "settings",
    ):
        assert f'data-view-panel="{view}"' in html
        assert f'data-view="{view}"' in html
    for copy in (
        "小镇此刻",
        "角色卡",
        "已经发生的事",
        "给林澄留言",
        "观察设置",
    ):
        assert copy in html
    assert "日记摘要" not in html
    assert "记忆摘要" not in html


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
        "/static/character-player.js",
        "/static/spine-player.js",
        "/static/vendor/spine-webgl.min.js",
        "/static/vendor/SPINE-RUNTIMES-LICENSE.txt",
        "/assets/manifest.json",
        "/assets/maps/town-map-world.webp",
        "/assets/buildings/dorm.webp",
        "/assets/buildings/classroom.webp",
        "/assets/buildings/library.webp",
        "/assets/buildings/canteen.webp",
        "/assets/buildings/river.webp",
        "/assets/buildings/shop.webp",
        "/assets/interiors/dorm.webp",
        "/assets/interiors/classroom.webp",
        "/assets/interiors/library.webp",
        "/assets/interiors/canteen.webp",
        "/assets/interiors/river.webp",
        "/assets/interiors/shop.webp",
        "/assets/portraits/lin_cheng.webp",
        "/assets/characters/lin_cheng.webp",
        "/assets/characters/whale-girl/whale-girl-manifest.json",
        "/assets/characters/whale-girl/lin-cheng-map.png",
        "/assets/characters/whale-girl/portraits/lin-cheng-hero.png",
        "/assets/characters/whale-girl/portraits/lin-cheng-calm.png",
        "/assets/characters/whale-girl/sheets/idle-down.webp",
        "/assets/characters/whale-girl/sheets/walk-right.webp",
        "/assets/spine/lin_cheng.json",
        "/assets/spine/lin_cheng.atlas",
        "/assets/spine/lin_cheng.png",
        "/assets/icons/map.png",
        "/assets/icons/settings.png",
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
    assert "grid-template-columns: repeat(5, 1fr)" in css
    assert "env(safe-area-inset-bottom)" in css
    assert "aspect-ratio: 16 / 9" in css
    assert ".world-plane" in css
    assert ".map-player" in css
    html = Path("web/index.html").read_text(encoding="utf-8")
    mobile_nav = html.split('<nav class="mobile-nav"', 1)[1].split('</nav>', 1)[0]
    assert 'data-view="settings"' in mobile_nav
    assert "@media (prefers-reduced-motion: reduce)" in css


def test_frontend_uses_only_frozen_public_api_fields() -> None:
    javascript = Path("web/app.js").read_text(encoding="utf-8")
    for endpoint in ("/world", "/agent", "/timeline", "/chat"):
        assert endpoint in javascript
    assert "/memory" not in javascript
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


def test_observer_loop_can_reach_world_character_and_chat(
    client: TestClient,
) -> None:
    world = client.get("/world")
    agent = client.get("/agent")
    chat = client.post("/chat", json={"message": "今天的校刊任务进展怎么样？"})
    assert world.status_code == 200
    assert agent.status_code == 200
    assert chat.status_code == 200
    assert client.get("/memory").status_code == 404
    assert world.json()["world"]["name"] == "青禾镇"
    assert world.json()["schema_version"] == "rpg-public-world-v2"
    assert world.json()["agent_presence"]["revision"] == world.json()["world"][
        "state_revision"
    ]
    assert agent.json()["agent"]["name"] == "林澄"
    assert chat.json()["status"] == "queued"


def test_b75_component_interfaces_are_reserved() -> None:
    html = Path("web/index.html").read_text(encoding="utf-8")
    css = Path("web/styles.css").read_text(encoding="utf-8")
    assert 'class="map-art world-map-stage"' in html
    assert 'class="portrait portrait-large"' in html
    assert 'class="nav-mark"' in html
    assert ".location-card" in css
    assert ".timeline-item" in css
    assert "[data-move]" not in css
    assert ".map-controls" not in css
    assert ".map-move-hint" not in css
    assert "/assets/maps/town-map-world.webp" in html
    assert "/assets/characters/whale-girl/portraits/lin-cheng-calm.png" in html
    assert 'id="world-plane"' in html
    assert 'id="map-player"' in html
    assert 'id="map-player-sprite"' in html
    assert "/static/character-player.js" in html
    assert "window.qingheCharacterPlayer?.initialize()" in Path(
        "web/app.js"
    ).read_text(encoding="utf-8")
    assert "data-move" not in html
    assert "MOVE_KEYS" not in Path("web/app.js").read_text(encoding="utf-8")
    assert 'id="location-dialog"' in html
    assert 'class="interior-scene"' in html
    assert "/assets/assets/" not in html


def test_b75_locations_open_their_matching_interior() -> None:
    javascript = Path("web/app.js").read_text(encoding="utf-8")
    for location_id, interior in (
        ("loc_dorm", "dorm"),
        ("loc_classroom", "classroom"),
        ("loc_library", "library"),
        ("loc_canteen", "canteen"),
        ("loc_shop", "shop"),
        ("loc_river", "river"),
    ):
        assert f'{location_id}: "{interior}"' in javascript
    assert "openLocationDialog" in javascript
    assert "requestAnimationFrame(mapAnimationFrame)" in javascript
    character_javascript = Path("web/character-player.js").read_text(
        encoding="utf-8"
    )
    assert "whale-girl-manifest.json" in character_javascript
    assert 'begin("turn"' in character_javascript
    assert 'begin("stop"' in character_javascript
    assert '"/assets/interiors/"' in javascript or "`/assets/interiors/" in javascript


def test_web_has_no_external_runtime_dependency(client: TestClient) -> None:
    html = client.get("/").text
    css = client.get("/static/styles.css").text
    javascript = client.get("/static/app.js").text
    combined = "\n".join((html, css, javascript))
    assert "cdn." not in combined
    assert "unpkg.com" not in combined
    assert "googleapis.com" not in combined
    assert "AIWORLD_LLM_API_KEY" not in combined
