from __future__ import annotations

import json
from pathlib import Path

from rpg_llm.runtime import LlmRuntimeConfig
from rpg_deploy.release import build_release, verify_release

ROOT = Path(__file__).resolve().parents[1]


def test_production_paths_are_outside_release_root() -> None:
    env_path = ROOT / "deploy" / "windows" / "production.env.example"
    values = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        key, value = line.split("=", 1)
        values[key] = value
    assert values["AIWORLD_SETUP_DIRECTORY"] == r"C:\AIWorld\data\setup"
    assert values["AIWORLD_PERSONA_DIRECTORY"] == r"C:\AIWorld\data\persona"
    assert values["AIWORLD_WORLD_CLOCK_DIRECTORY"] == r"C:\AIWorld\data\world"
    assert values["AIWORLD_LLM_API_KEY_FILE"] == (
        r"C:\AIWorld\data\setup\deepseek_api_key.txt"
    )
    assert values["AIWORLD_PRODUCT_DATABASE_URL"].startswith(
        "postgresql+psycopg://"
    )
    for key in (
        "AIWORLD_SETUP_DIRECTORY",
        "AIWORLD_PERSONA_DIRECTORY",
        "AIWORLD_WORLD_CLOCK_DIRECTORY",
    ):
        assert not values[key].lower().startswith(r"c:\aiworld\current")


def test_setup_and_persona_routes_are_admin_only_in_proxy_templates() -> None:
    nginx = (
        ROOT / "deploy" / "reverse-proxy" / "nginx.conf.template"
    ).read_text(encoding="utf-8")
    caddy = (
        ROOT / "deploy" / "reverse-proxy" / "Caddyfile.template"
    ).read_text(encoding="utf-8")
    for path in ("/api/setup/", "/api/persona/", "/setup"):
        assert path in nginx
        assert path in caddy
    assert nginx.count("allow __ADMIN_CIDR__;") >= 3
    assert nginx.count("deny all;") >= 3
    assert 'Cache-Control "no-store"' in nginx
    assert "@setup_denied" in caddy
    assert "not remote_ip 127.0.0.1 ::1 {$AIWORLD_ADMIN_CIDR}" in caddy
    assert 'header Cache-Control "no-store"' in caddy


def test_world_tick_task_is_registered_for_ten_minutes() -> None:
    register = (
        ROOT / "deploy" / "windows" / "Register-AIWorldTasks.ps1"
    ).read_text(encoding="utf-8")
    unregister = (
        ROOT / "deploy" / "windows" / "Unregister-AIWorldTasks.ps1"
    ).read_text(encoding="utf-8")
    tick = (
        ROOT / "deploy" / "windows" / "Invoke-AIWorldWorldTick.ps1"
    ).read_text(encoding="utf-8")
    assert "AIWorld-WorldTick" in register
    assert "AIWorld-WorldTick" in unregister
    assert "New-TimeSpan -Minutes 10" in register
    assert "app.world_clock" in tick
    assert "world-tick.log" in tick


def test_release_contains_no_runtime_data(tmp_path) -> None:
    output = tmp_path / "release"
    manifest = build_release(
        ROOT,
        output,
        version="0.2.0-test",
        built_at="2026-11-07T00:00:00Z",
    )
    paths = {entry["path"] for entry in manifest["files"]}
    assert not any(path.startswith("data/") for path in paths)
    assert not any(
        path.startswith(("logs/", "backups/"))
        for path in paths
    )
    assert verify_release(output) == []


def test_external_data_is_independent_of_release_switch(tmp_path) -> None:
    release_a = tmp_path / "releases" / "a"
    release_b = tmp_path / "releases" / "b"
    data_dir = tmp_path / "data"
    release_a.mkdir(parents=True)
    release_b.mkdir(parents=True)
    setup_dir = data_dir / "setup"
    persona_dir = data_dir / "persona"
    world_dir = data_dir / "world"
    for directory in (setup_dir, persona_dir, world_dir):
        directory.mkdir(parents=True)
    sentinels = {
        setup_dir / "deepseek_api_key.txt": "sk-test-switch",
        persona_dir / "persona.json": '{"revision": 2}',
        world_dir / "world_clock.json": '{"state_revision": 52}',
    }
    for path, content in sentinels.items():
        path.write_text(content, encoding="utf-8")

    current_release = release_a
    current_release = release_b
    assert current_release == release_b
    assert not data_dir.is_relative_to(current_release)
    assert all(path.read_text(encoding="utf-8") for path in sentinels)


def test_runtime_can_read_deepseek_key_from_private_file(
    tmp_path,
    monkeypatch,
) -> None:
    key_path = tmp_path / "deepseek_api_key.txt"
    key_path.write_text("sk-test-file-r5\n", encoding="utf-8")
    monkeypatch.setenv("AIWORLD_LLM_PROVIDER", "deepseek")
    monkeypatch.delenv("AIWORLD_LLM_API_KEY", raising=False)
    monkeypatch.setenv("AIWORLD_LLM_API_KEY_FILE", str(key_path))
    config = LlmRuntimeConfig.from_env()
    assert config.api_key == "sk-test-file-r5"
    assert config.safe_summary()["api_key_configured"] is True
    assert str(key_path) not in json.dumps(config.safe_summary())
