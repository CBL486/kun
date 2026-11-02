from __future__ import annotations

import json
import tomllib
from pathlib import Path

from fastapi.testclient import TestClient

from app.local_state import LocalWorldStore
from app.main import create_app
from rpg_deploy.release import (
    build_release,
    validate_template_directory,
    verify_release,
)
from rpg_orm.migrations import create_database_engine
from rpg_scheduler import PersistentMessageQueue, ScheduleSpec, SchedulerRepository


ROOT = Path(__file__).resolve().parents[1]


async def ready_true() -> bool:
    return True


def test_metrics_endpoint_exposes_only_operational_data() -> None:
    client = TestClient(
        create_app(
            store=LocalWorldStore(),
            readiness_check=ready_true,
        )
    )
    try:
        response = client.get("/metrics")
    finally:
        client.close()
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    body = response.text
    assert "aiworld_up 1" in body
    assert "aiworld_database_ready 1" in body
    assert "aiworld_http_requests_total" in body
    assert "aiworld_scheduler_database_configured 0" in body
    assert "AIWORLD_LLM_API_KEY" not in body
    assert "password" not in body.lower()


def test_metrics_include_scheduler_backlog(tmp_path) -> None:
    engine = create_database_engine(
        f"sqlite:///{(tmp_path / 'metrics.db').as_posix()}"
    )
    queue = PersistentMessageQueue(engine)
    SchedulerRepository(engine).enqueue(
        ScheduleSpec(
            kind="memory_reconcile",
            operation_id="op_b12_metrics",
            payload={},
        )
    )
    client = TestClient(
        create_app(
            store=LocalWorldStore(),
            message_store=queue,
            readiness_check=ready_true,
        )
    )
    try:
        body = client.get("/metrics").text
    finally:
        client.close()
        engine.dispose()
    assert "aiworld_scheduler_database_configured 1" in body
    assert "aiworld_scheduler_pending_due 1" in body
    assert "aiworld_scheduler_expired_leases 0" in body


def test_proxy_and_monitoring_templates_are_safe() -> None:
    assert validate_template_directory(ROOT) == []
    nginx = (
        ROOT / "deploy" / "reverse-proxy" / "nginx.conf.template"
    ).read_text(encoding="utf-8")
    caddy = (
        ROOT / "deploy" / "reverse-proxy" / "Caddyfile.template"
    ).read_text(encoding="utf-8")
    assert "location = /metrics" in nginx
    assert "deny all" in nginx
    assert "limit_req zone=aiworld_api" in nginx
    assert "Cache-Control" in nginx
    assert "@metrics path /metrics" in caddy
    assert "respond @metrics 404" in caddy


def test_release_build_is_complete_and_excludes_sensitive_files(tmp_path) -> None:
    output = tmp_path / "aiworld-release"
    manifest = build_release(
        ROOT,
        output,
        version="0.1.0-test",
        built_at="2026-11-01T00:00:00Z",
    )
    assert manifest["version"] == "0.1.0-test"
    assert manifest["database_schema_version"] == 4
    on_disk = json.loads(
        (output / "RELEASE_MANIFEST.json").read_text(encoding="utf-8")
    )
    assert on_disk["package_sha256"] == manifest["package_sha256"]
    assert verify_release(output) == []
    paths = {item["path"] for item in manifest["files"]}
    assert "app/main.py" in paths
    assert "assets/manifest.json" in paths
    assert "deploy/reverse-proxy/nginx.conf.template" in paths
    assert "rpg_deploy/__main__.py" in paths
    assert "rpg_deploy/release.py" in paths
    assert "scripts/write_runtime_env.py" in paths
    assert "docs/staging-validation-v1.md" in paths
    assert "docs/staging-evidence-v1.json" in paths
    assert "docs/deepseek-production-v1.md" in paths
    assert "docs/deepseek-smoke-evidence-2026-11-02.json" in paths
    assert "docs/production-env-deepseek-2026-11-02.json" in paths
    assert not any(path.startswith("tests/") for path in paths)
    assert not any(path.startswith("out/") for path in paths)
    assert not any(name in {".env", ".env.local"} for name in paths)
    assert not any(
        Path(path).suffix.lower()
        in {".db", ".sqlite", ".sqlite3", ".key", ".pem", ".zip", ".rar"}
        for path in paths
    )



def test_switch_script_uses_bundled_release_verifier() -> None:
    script = (ROOT / "deploy" / "windows" / "Switch-AIWorldRelease.ps1").read_text(
        encoding="utf-8"
    )
    assert "from rpg_deploy.__main__ import main" in script
    assert "-m rpg_deploy verify" not in script


def test_release_verifier_ignores_runtime_generated_python_files(tmp_path) -> None:
    output = tmp_path / "generated-release"
    build_release(ROOT, output, version="0.1.0-test")
    cache = output / "app" / "__pycache__"
    cache.mkdir()
    (cache / "main.cpython-312.pyc").write_bytes(b"cache")
    (output / "app" / "generated.pyc").write_bytes(b"cache")
    assert verify_release(output) == []


def test_server_extra_declares_async_and_sync_postgres_drivers() -> None:
    payload = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    server = payload["project"]["optional-dependencies"]["server"]
    assert any(dep.startswith("asyncpg") for dep in server)
    assert any(dep.startswith("psycopg[binary]") for dep in server)

def test_release_verifier_detects_tampering(tmp_path) -> None:
    output = tmp_path / "tampered-release"
    build_release(ROOT, output, version="0.1.0-test")
    target = output / "app" / "main.py"
    target.write_text(
        target.read_text(encoding="utf-8") + "\n# tampered\n",
        encoding="utf-8",
    )
    issues = verify_release(output)
    assert "sha256:app/main.py" in issues
    assert "size:app/main.py" in issues


def test_release_manifest_is_deterministic(tmp_path) -> None:
    first = tmp_path / "release-a"
    second = tmp_path / "release-b"
    manifest_a = build_release(
        ROOT,
        first,
        version="0.1.0-test",
        built_at="2026-11-01T00:00:00Z",
    )
    manifest_b = build_release(
        ROOT,
        second,
        version="0.1.0-test",
        built_at="2026-11-01T00:00:00Z",
    )
    assert manifest_a["files"] == manifest_b["files"]
    assert (
        (first / "RELEASE_MANIFEST.json").read_bytes()
        == (second / "RELEASE_MANIFEST.json").read_bytes()
    )


def test_deployment_docs_and_scripts_are_present() -> None:
    required = (
        "docs/deployment-checklist.md",
        "docs/rollback-runbook.md",
        "docs/deployment-topology-v1.md",
        "deploy/windows/Register-AIWorldTasks.ps1",
        "deploy/windows/health-check.ps1",
        "deploy/windows/Rotate-AIWorldLogs.ps1",
        "scripts/build-release.ps1",
        "scripts/verify-release.ps1",
    )
    for relative in required:
        assert (ROOT / relative).is_file(), relative
