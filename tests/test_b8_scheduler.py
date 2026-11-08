from __future__ import annotations

import copy
import os
import subprocess
import tempfile
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect

from app.main import create_app
from app.local_state import LocalWorldStore
from rpg_agent.loop import AgentLoop
from rpg_orm.migrations import (
    LATEST_SCHEMA_VERSION,
    create_database_engine,
    migrate,
    schema_version,
)
from rpg_orm.repository import OrmRepository
from rpg_scheduler import (
    PersistentMessageQueue,
    ScheduleSpec,
    SchedulerRepository,
    SchedulerService,
)
from rpg_scheduler.errors import SchedulerError
from rpg_scheduler.locks import advisory_lock
from rpg_sim.engine import WorldEngine
from rpg_sim.scenario import initial_world

try:
    import pgserver
    import pgserver.postgres_server as pgserver_module
    from pgserver._commands import POSTGRES_BIN_PATH

    PG_SERVER_AVAILABLE = True
except ImportError:
    PG_SERVER_AVAILABLE = False


BASE_TIME = datetime(2026, 11, 1, 0, 0, tzinfo=timezone.utc)


def make_engine(path: Path):
    return create_database_engine(f"sqlite:///{path.as_posix()}")


def make_fixture() -> dict:
    loop = AgentLoop(WorldEngine(initial_world()))
    loop.prepare("2026-11-02", "08:00", "morning_1")
    before = copy.deepcopy(loop.engine.snapshot())
    step = loop.run_once("op_b8_event_001")
    if not step.world_result["ok"]:
        raise AssertionError(step.world_result)
    return {
        "before": before,
        "after": loop.engine.snapshot(),
        "action": step.intent.to_dict(),
        "event": step.world_result["event"],
    }


def test_schema_version_two_adds_scheduler_and_message_tables(tmp_path) -> None:
    engine = make_engine(tmp_path / "schema.db")
    try:
        assert migrate(engine) == LATEST_SCHEMA_VERSION
        tables = set(inspect(engine).get_table_names())
        assert {
            "scheduled_tasks",
            "observer_messages",
        } <= tables
    finally:
        engine.dispose()


def test_enqueue_is_operation_idempotent_and_conflicts_on_payload(tmp_path) -> None:
    engine = make_engine(tmp_path / "idempotent.db")
    try:
        repository = SchedulerRepository(engine)
        spec = ScheduleSpec(
            kind="memory_reconcile",
            operation_id="op_b8_enqueue_001",
            payload={"until": "2026-11-01T00:00:00Z"},
            available_at=BASE_TIME,
        )
        first = repository.enqueue(spec)
        replay = repository.enqueue(spec)
        assert first["replayed"] is False
        assert replay["replayed"] is True
        assert first["task_id"] == replay["task_id"]

        changed = ScheduleSpec(
            kind=spec.kind,
            operation_id=spec.operation_id,
            payload={"until": "2026-11-02T00:00:00Z"},
            available_at=BASE_TIME,
        )
        with pytest.raises(SchedulerError) as caught:
            repository.enqueue(changed)
        assert caught.value.code == "duplicate_operation"
    finally:
        engine.dispose()


def test_worker_commits_business_result_only_once(tmp_path) -> None:
    engine = make_engine(tmp_path / "execute.db")
    try:
        world_repository = OrmRepository(engine)
        fixture = make_fixture()
        world_repository.initialize_world(fixture["before"])
        scheduler_repository = SchedulerRepository(engine)
        service = SchedulerService(scheduler_repository)
        spec = ScheduleSpec(
            kind="world_command",
            operation_id=fixture["action"]["operation_id"],
            payload={"action": fixture["action"]},
            available_at=BASE_TIME,
        )
        calls = 0

        def handler(_task: dict) -> dict:
            nonlocal calls
            calls += 1
            return world_repository.commit_step(
                state_before=fixture["before"],
                state_after=fixture["after"],
                event=fixture["event"],
                action=fixture["action"],
            ).to_dict()

        scheduled = service.schedule(spec)
        first = service.run_next(
            worker_id="worker-a",
            handlers={"world_command": handler},
            now=BASE_TIME,
        )
        replay = service.schedule(spec)
        duplicate_run = service.run_next(
            worker_id="worker-a",
            handlers={"world_command": handler},
            now=BASE_TIME,
        )
        assert scheduled.replayed is False
        assert first.status == "succeeded"
        assert replay.replayed is True
        assert duplicate_run.status == "idle"
        assert calls == 1
        assert len(world_repository.list_actions()) == 1
        assert len(world_repository.list_events()) == 1
    finally:
        engine.dispose()


def test_expired_lease_is_recovered_and_old_worker_is_rejected(tmp_path) -> None:
    engine = make_engine(tmp_path / "lease.db")
    try:
        repository = SchedulerRepository(engine)
        spec = ScheduleSpec(
            kind="memory_reconcile",
            operation_id="op_b8_lease_001",
            payload={},
            available_at=BASE_TIME,
            max_attempts=3,
        )
        repository.enqueue(spec)
        first = repository.claim_next(
            worker_id="worker-a",
            now=BASE_TIME,
            lease_seconds=5,
        )
        assert first is not None
        assert repository.claim_next(
            worker_id="worker-b",
            now=BASE_TIME,
            lease_seconds=5,
        ) is None

        recovered = repository.recover_expired(
            now=BASE_TIME + timedelta(seconds=6)
        )
        assert recovered == {"released": 1, "dead_lettered": 0}
        second = repository.claim_next(
            worker_id="worker-b",
            now=BASE_TIME + timedelta(seconds=6),
            lease_seconds=5,
        )
        assert second is not None
        assert second["attempts"] == 2
        with pytest.raises(SchedulerError) as caught:
            repository.succeed(
                task_id=first["task_id"],
                worker_id="worker-a",
                result={"stale": True},
                now=BASE_TIME + timedelta(seconds=6),
            )
        assert caught.value.code == "lease_lost"
    finally:
        engine.dispose()


def test_priority_and_backlog_visibility(tmp_path) -> None:
    engine = make_engine(tmp_path / "backlog.db")
    try:
        repository = SchedulerRepository(engine)
        for index, priority in enumerate((1, 10, 5)):
            repository.enqueue(
                ScheduleSpec(
                    kind="probe",
                    operation_id=f"op_b8_backlog_{index}",
                    payload={"index": index},
                    available_at=BASE_TIME,
                    priority=priority,
                )
            )
        repository.enqueue(
            ScheduleSpec(
                kind="probe",
                operation_id="op_b8_delayed_001",
                payload={},
                available_at=BASE_TIME + timedelta(minutes=1),
            )
        )
        backlog = repository.backlog(now=BASE_TIME)
        assert backlog["pending_due"] == 3
        assert backlog["delayed"] == 1
        assert backlog["oldest_pending_seconds"] >= 0

        first = repository.claim_next(
            worker_id="priority-worker",
            now=BASE_TIME,
            lease_seconds=30,
        )
        second = repository.claim_next(
            worker_id="priority-worker",
            now=BASE_TIME,
            lease_seconds=30,
        )
        assert first is not None
        assert second is not None
        assert first["payload"] == {"index": 1}
        assert second["payload"] == {"index": 2}
    finally:
        engine.dispose()


def test_timeout_backlog_and_dead_letter_are_observable(tmp_path) -> None:
    engine = make_engine(tmp_path / "timeout.db")
    try:
        repository = SchedulerRepository(engine)
        service = SchedulerService(repository)
        spec = ScheduleSpec(
            kind="slow",
            operation_id="op_b8_timeout_001",
            payload={},
            available_at=BASE_TIME,
            max_attempts=1,
            timeout_seconds=0.02,
        )
        service.schedule(spec)
        backlog = repository.backlog(now=BASE_TIME)
        assert backlog["pending_due"] == 1

        outcome = service.run_next(
            worker_id="worker-timeout",
            handlers={"slow": lambda _task: time.sleep(0.2)},
            now=BASE_TIME,
        )
        assert outcome.status == "dead_letter"
        assert outcome.error == "TimeoutError"
        stored = repository.get_by_operation(spec.operation_id)
        assert stored is not None
        assert stored["status"] == "dead_letter"
        assert stored["attempts"] == 1
        assert repository.backlog(now=BASE_TIME)["expired_leases"] == 0
    finally:
        engine.dispose()


def test_retry_uses_backoff_and_attempt_budget(tmp_path) -> None:
    engine = make_engine(tmp_path / "retry.db")
    try:
        repository = SchedulerRepository(engine)
        service = SchedulerService(repository)
        spec = ScheduleSpec(
            kind="flaky",
            operation_id="op_b8_retry_001",
            payload={},
            available_at=BASE_TIME,
            max_attempts=2,
            timeout_seconds=1,
        )
        service.schedule(spec)
        attempts = 0

        def handler(_task: dict) -> dict:
            nonlocal attempts
            attempts += 1
            if attempts == 1:
                raise RuntimeError("transient_failure")
            return {"attempt": attempts}

        first = service.run_next(
            worker_id="worker-retry",
            handlers={"flaky": handler},
            now=BASE_TIME,
        )
        assert first.status == "pending"
        assert first.error == "RuntimeError"
        assert repository.backlog(now=BASE_TIME)["delayed"] == 1
        assert service.run_next(
            worker_id="worker-retry",
            handlers={"flaky": handler},
            now=BASE_TIME,
        ).status == "idle"

        second = service.run_next(
            worker_id="worker-retry",
            handlers={"flaky": handler},
            now=BASE_TIME + timedelta(seconds=2),
        )
        assert second.status == "succeeded"
        assert second.result == {"attempt": 2}
    finally:
        engine.dispose()


def test_persistent_message_queue_survives_store_restart(tmp_path) -> None:
    engine = make_engine(tmp_path / "messages.db")
    try:
        queue = PersistentMessageQueue(engine)
        first = LocalWorldStore(message_store=queue)
        response = first.chat("请记录今天的校刊进度。")
        second = LocalWorldStore(message_store=queue)
        messages = second.queued_messages()
        assert response.status == "delivered"
        assert len(messages) == 1
        assert messages[0]["message_id"] == response.message_id
        assert messages[0]["message"] == "请记录今天的校刊进度。"
        assert messages[0]["status"] == "queued"
    finally:
        engine.dispose()


def test_api_message_survives_app_restart(tmp_path) -> None:
    engine = make_engine(tmp_path / "api-messages.db")
    try:
        queue = PersistentMessageQueue(engine)
        first_client = TestClient(create_app(message_store=queue))
        response = first_client.post(
            "/chat",
            json={"message": "请留意今晚的值日安排。"},
        )
        first_client.close()
        assert response.status_code == 200

        second_client = TestClient(create_app(message_store=queue))
        messages = second_client.app.state.local_world.queued_messages()
        second_client.close()
        assert len(messages) == 1
        assert messages[0]["message_id"] == response.json()["message_id"]
    finally:
        engine.dispose()


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


@pytest.mark.skipif(
    not PG_SERVER_AVAILABLE,
    reason="未安装本地 pgserver 测试依赖",
)
def test_postgres_advisory_lock_blocks_second_acquire() -> None:
    _install_windows_safe_pg_commands()
    with tempfile.TemporaryDirectory() as temporary:
        server = pgserver.get_server(
            Path(temporary) / "pgdata",
            cleanup_mode="delete",
        )
        engine = create_database_engine(server.get_uri())
        try:
            repository = SchedulerRepository(engine)
            repository.enqueue(
                ScheduleSpec(
                    kind="postgres_probe",
                    operation_id="op_b8_postgres_001",
                    payload={},
                    available_at=BASE_TIME,
                )
            )
            claimed = repository.claim_next(
                worker_id="postgres-worker",
                now=BASE_TIME,
                lease_seconds=1,
            )
            assert claimed is not None
            assert repository.recover_expired(
                now=BASE_TIME + timedelta(seconds=2)
            )["released"] == 1

            with advisory_lock(engine, "same-operation") as first:
                with advisory_lock(engine, "same-operation") as second:
                    assert first is True
                    assert second is False
            with advisory_lock(engine, "same-operation") as reacquired:
                assert reacquired is True
        finally:
            engine.dispose()
            server.cleanup()
