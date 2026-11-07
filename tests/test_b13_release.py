from __future__ import annotations

import copy
import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import inspect

from app.local_state import LocalWorldStore
from app.main import create_app
from app.settings import settings
from fastapi.testclient import TestClient
from rpg_agent.loop import AgentLoop
from rpg_deploy.release import build_release, verify_release
from rpg_orm.migrations import (
    create_database_engine,
    migrate,
    rollback,
)
from rpg_orm.repository import OrmRepository
from rpg_release.backup import (
    backup_database,
    inspect_database,
    restore_database,
    verify_backup,
)
from rpg_release.evidence import build_release_evidence
from rpg_sim.engine import WorldEngine
from rpg_sim.scenario import initial_world

try:
    import pgserver
    import pgserver.postgres_server as pgserver_module
    from pgserver._commands import POSTGRES_BIN_PATH

    PG_SERVER_AVAILABLE = True
except ImportError:
    PG_SERVER_AVAILABLE = False


ROOT = Path(__file__).resolve().parents[1]


def leave_one_committed_event(repository: OrmRepository) -> dict:
    loop = AgentLoop(WorldEngine(initial_world()))
    loop.prepare("2026-11-02", "08:00", "morning_1")
    before = copy.deepcopy(loop.engine.snapshot())
    step = loop.run_once("op_b13_backup_001")
    if not step.world_result["ok"]:
        raise AssertionError(step.world_result)
    repository.initialize_world(before)
    repository.commit_step(
        state_before=before,
        state_after=loop.engine.snapshot(),
        event=step.world_result["event"],
        action=step.intent.to_dict(),
    )
    return step.world_result["event"]


def _install_windows_safe_pg_commands() -> None:
    def make_command(name: str):
        executable = name if os.name == "nt" else name.removesuffix(".exe")
        encoding = "gbk" if os.name == "nt" else "utf-8"

        def command(args, pgdata=None, **kwargs):
            if pgdata is None:
                raise ValueError("pgdata required")
            full_command = [
                str(POSTGRES_BIN_PATH / executable),
                "-D",
                str(pgdata),
                *args,
            ]
            with (
                tempfile.TemporaryFile(
                    "w+",
                    encoding=encoding,
                    errors="replace",
                ) as stdout,
                tempfile.TemporaryFile(
                    "w+",
                    encoding=encoding,
                    errors="replace",
                ) as stderr,
            ):
                subprocess.run(
                    full_command,
                    check=True,
                    stdout=stdout,
                    stderr=stderr,
                    text=True,
                    **kwargs,
                )
                stdout.seek(0)
                stderr.seek(0)
                return stdout.read()

        return command

    pgserver_module.initdb = make_command("initdb.exe")
    pgserver_module.pg_ctl = make_command("pg_ctl.exe")


def test_sqlite_backup_restore_preserves_key_rows(tmp_path) -> None:
    source = tmp_path / "source.sqlite3"
    target = tmp_path / "restored.sqlite3"
    backup = tmp_path / "backup.sqlite3"
    engine = create_database_engine(f"sqlite:///{source.as_posix()}")
    try:
        migrate(engine)
        repository = OrmRepository(engine)
        event = leave_one_committed_event(repository)
        before = inspect_database(f"sqlite:///{source.as_posix()}")
        metadata = backup_database(
            database_url=f"sqlite:///{source.as_posix()}",
            output=backup,
        )
        assert metadata["key_counts"]["events"] == 1
        assert verify_backup(backup) == []
        result = restore_database(
            backup=backup,
            database_url=f"sqlite:///{target.as_posix()}",
            confirm_restore=True,
        )
        after = inspect_database(f"sqlite:///{target.as_posix()}")
        assert result["verified"] is True
        assert before["schema_version"] == after["schema_version"] == 5
        assert before["key_counts"] == after["key_counts"]
        restored_engine = create_database_engine(
            f"sqlite:///{target.as_posix()}"
        )
        try:
            restored = OrmRepository(restored_engine)
            assert restored.get_event(event["event_id"]) is not None
        finally:
            restored_engine.dispose()
    finally:
        engine.dispose()


def test_backup_checksum_detects_tampering(tmp_path) -> None:
    source = tmp_path / "tamper-source.sqlite3"
    backup = tmp_path / "tamper.sqlite3"
    engine = create_database_engine(f"sqlite:///{source.as_posix()}")
    try:
        migrate(engine)
    finally:
        engine.dispose()
    backup_database(
        database_url=f"sqlite:///{source.as_posix()}",
        output=backup,
    )
    with backup.open("ab") as handle:
        handle.write(b"tampered")
    assert "sha256_mismatch" in verify_backup(backup)


def test_release_evidence_contains_reproducible_and_license_fields() -> None:
    evidence = build_release_evidence(ROOT)
    assert evidence["schema_version"] == "rpg-release-evidence-v1"
    assert evidence["database_schema_version"] == 5
    assert evidence["e2e"]["status"] == "passed"
    assert evidence["cost"]["bill_matches"] is True
    assert evidence["assets"]["authorized"] is True
    assert evidence["assets"]["asset_count"] > 0
    serialized = json.dumps(evidence, ensure_ascii=False)
    assert "AIWORLD_LLM_API_KEY" not in serialized


def test_release_package_contains_recovery_tools_and_no_private_data(
    tmp_path,
) -> None:
    output = tmp_path / "b13-release"
    manifest = build_release(
        ROOT,
        output,
        version="0.1.0-b13-test",
        built_at="2026-11-01T00:00:00Z",
    )
    paths = {item["path"] for item in manifest["files"]}
    assert "rpg_release/backup.py" in paths
    assert "deploy/windows/Invoke-AIWorldBackup.ps1" in paths
    assert "docs/release-evidence.json" in paths
    assert not any(path.startswith("tests/") for path in paths)
    assert not any(
        path.startswith("backups/") or path.startswith("data/")
        for path in paths
    )
    assert verify_release(output) == []


async def ready_true() -> bool:
    return True


def test_metrics_expose_backup_age(tmp_path, monkeypatch) -> None:
    backup = tmp_path / "aiworld-20261101T000000Z.dump"
    backup.write_bytes(b"backup")
    old_time = 1_800_000_000
    os.utime(backup, (old_time, old_time))
    monkeypatch.setattr(settings, "backup_directory", str(tmp_path))
    client = TestClient(
        create_app(
            store=LocalWorldStore(),
            readiness_check=ready_true,
        )
    )
    try:
        body = client.get("/metrics").text
    finally:
        client.close()
    assert "aiworld_backup_age_seconds " in body


@pytest.mark.skipif(
    not PG_SERVER_AVAILABLE,
    reason="未安装本地 pgserver 测试依赖",
)
def test_postgres_backup_restore_preserves_key_rows() -> None:
    _install_windows_safe_pg_commands()
    with tempfile.TemporaryDirectory() as temporary:
        temporary_path = Path(temporary)
        server = pgserver.get_server(
            temporary_path / "pgdata",
            cleanup_mode="delete",
        )
        url = server.get_uri()
        engine = create_database_engine(url)
        backup = temporary_path / "postgres.dump"
        try:
            migrate(engine)
            repository = OrmRepository(engine)
            event = leave_one_committed_event(repository)
            before = inspect_database(url)
            metadata = backup_database(
                database_url=url,
                output=backup,
                pg_bin=POSTGRES_BIN_PATH,
            )
            assert metadata["backend"] == "postgresql"
            assert verify_backup(backup) == []
            rollback(engine)
            migrate(engine)
            result = restore_database(
                backup=backup,
                database_url=url,
                confirm_restore=True,
                pg_bin=POSTGRES_BIN_PATH,
            )
            after = inspect_database(url)
            assert result["verified"] is True
            assert before["key_counts"] == after["key_counts"]
            restored = OrmRepository(engine)
            assert restored.get_event(event["event_id"]) is not None
        finally:
            engine.dispose()
            server.cleanup()
