from __future__ import annotations

import copy
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

import sqlalchemy
from sqlalchemy import inspect

from rpg_agent.loop import AgentLoop
from rpg_orm.migrations import (
    create_database_engine,
    migrate,
    rollback,
    schema_version,
)
from rpg_orm.repository import OrmRepository
from rpg_sim.engine import WorldEngine
from rpg_sim.scenario import initial_world

try:
    import pgserver
    import pgserver.postgres_server as pgserver_module
    from pgserver._commands import POSTGRES_BIN_PATH

    PG_SERVER_AVAILABLE = True
except ImportError:
    PG_SERVER_AVAILABLE = False


def make_fixture() -> dict:
    loop = AgentLoop(WorldEngine(initial_world()))
    loop.prepare("2026-11-02", "08:00", "morning_1")
    before = copy.deepcopy(loop.engine.snapshot())
    step = loop.run_once("op_b5_fixture_001")
    if not step.world_result["ok"]:
        raise AssertionError(step.world_result)
    return {
        "before": before,
        "after": loop.engine.snapshot(),
        "action": step.intent.to_dict(),
        "event": step.world_result["event"],
        "scope": {
            "tenant_id": "rpg-world",
            "world_id": "world_qinghe_v1",
            "user_id": "observer_demo_001",
            "character_id": "char_lin_cheng",
            "surface": "school",
            "conversation_id": "day-2026-11-02",
        },
    }


def reset_schema(engine) -> None:
    rollback(engine)
    migrate(engine)


class SQLiteContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        database = Path(self.temporary.name) / "b5-sqlite.db"
        self.engine = create_database_engine(f"sqlite:///{database.as_posix()}")

    def tearDown(self) -> None:
        self.engine.dispose()
        self.temporary.cleanup()

    def test_sqlite_migration_is_repeatable_and_rollback_drops_schema(self) -> None:
        self.assertEqual(1, migrate(self.engine))
        self.assertEqual(1, migrate(self.engine))
        self.assertEqual(1, schema_version(self.engine))
        self.assertIn("memories", inspect(self.engine).get_table_names())
        self.assertEqual(0, rollback(self.engine))
        self.assertEqual(0, schema_version(self.engine))
        self.assertNotIn("memories", inspect(self.engine).get_table_names())

    def test_sqlite_null_json_and_timezone_mapping(self) -> None:
        migrate(self.engine)
        repo = OrmRepository(self.engine)
        fixture = make_fixture()
        repo.initialize_world(fixture["before"])
        result = repo.commit_step(
            state_before=fixture["before"],
            state_after=fixture["after"],
            event=fixture["event"],
            action=fixture["action"],
        )
        self.assertEqual("projected", result.status)
        event = repo.list_events()[0]
        self.assertEqual("2026-11-02T00:00:00Z", event["occurred_at"])
        self.assertIsInstance(event["event"]["memory_candidates"], list)
        columns = {
            column["name"]: column
            for column in inspect(self.engine).get_columns("memories")
        }
        self.assertTrue(columns["conversation_id"]["nullable"])
        self.assertFalse(columns["scope_hash"]["nullable"])

    def test_sqlite_replay_is_idempotent(self) -> None:
        migrate(self.engine)
        repo = OrmRepository(self.engine)
        fixture = make_fixture()
        repo.initialize_world(fixture["before"])
        first = repo.commit_step(
            state_before=fixture["before"],
            state_after=fixture["after"],
            event=fixture["event"],
            action=fixture["action"],
        )
        replay = repo.commit_step(
            state_before=fixture["before"],
            state_after=fixture["after"],
            event=fixture["event"],
            action=fixture["action"],
        )
        self.assertFalse(first.replayed)
        self.assertTrue(replay.replayed)
        self.assertEqual(1, len(repo.list_actions()))
        self.assertEqual(1, len(repo.list_events()))
        self.assertEqual(1, len(repo.semantic_export()["memories"]))


@unittest.skipUnless(PG_SERVER_AVAILABLE, "未安装本地 pgserver 测试依赖")
class PostgreSQLContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._install_windows_safe_pg_commands()
        cls.temporary = tempfile.TemporaryDirectory()
        pgdata = Path(cls.temporary.name) / "pgdata"
        cls.server = pgserver.get_server(pgdata, cleanup_mode="delete")
        cls.engine = create_database_engine(cls.server.get_uri())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.engine.dispose()
        cls.server.cleanup()
        cls.temporary.cleanup()

    def setUp(self) -> None:
        reset_schema(self.engine)

    @staticmethod
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

    def test_postgres_migration_and_rollback(self) -> None:
        self.assertEqual(1, schema_version(self.engine))
        self.assertEqual(0, rollback(self.engine))
        self.assertEqual(0, schema_version(self.engine))
        self.assertEqual(1, migrate(self.engine))
        self.assertEqual(1, migrate(self.engine))

    def test_postgres_uses_jsonb_and_timezone_aware_datetime(self) -> None:
        columns = {
            column["name"]: column
            for column in inspect(self.engine).get_columns("memories")
        }
        self.assertIn("JSONB", str(columns["scene_tags"]["type"]).upper())
        self.assertIn("TIMESTAMP", str(columns["created_at"]["type"]).upper())
        self.assertTrue(columns["conversation_id"]["nullable"])

    def test_same_fixture_has_same_business_digest_on_both_backends(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sqlite_engine = create_database_engine(
                f"sqlite:///{(Path(temporary) / 'compare.db').as_posix()}"
            )
            try:
                migrate(sqlite_engine)
                sqlite_repo = OrmRepository(sqlite_engine)
                postgres_repo = OrmRepository(self.engine)
                fixture = make_fixture()
                for repo in (sqlite_repo, postgres_repo):
                    repo.initialize_world(copy.deepcopy(fixture["before"]))
                    repo.commit_step(
                        state_before=copy.deepcopy(fixture["before"]),
                        state_after=copy.deepcopy(fixture["after"]),
                        event=copy.deepcopy(fixture["event"]),
                        action=copy.deepcopy(fixture["action"]),
                    )
                sqlite_export = sqlite_repo.semantic_export()
                postgres_export = postgres_repo.semantic_export()
                self.assertEqual(
                    sqlite_export["digest"],
                    postgres_export["digest"],
                )
                self.assertEqual(
                    sqlite_export["memories"],
                    postgres_export["memories"],
                )
            finally:
                sqlite_engine.dispose()

    def test_projection_failure_reconciles_on_postgres(self) -> None:
        repo = OrmRepository(self.engine)
        fixture = make_fixture()
        repo.initialize_world(fixture["before"])
        result = repo.commit_step(
            state_before=fixture["before"],
            state_after=fixture["after"],
            event=fixture["event"],
            action=fixture["action"],
            simulate_projection_failure=True,
        )
        self.assertEqual("reconciliation_required", result.status)
        self.assertEqual(1, len(repo.list_projections("pending")))
        self.assertEqual(0, len(repo.semantic_export()["memories"]))
        self.assertEqual(1, repo.reconcile(fixture["event"]["event_id"])["projected"])
        self.assertEqual(1, len(repo.semantic_export()["memories"]))

    def test_postgres_indexes_and_checks_exist(self) -> None:
        inspector = inspect(self.engine)
        indexes = {
            item["name"]
            for item in inspector.get_indexes("memories")
        }
        self.assertIn("idx_memories_scope_state", indexes)
        self.assertIn("idx_memories_source_event", indexes)
        checks = {
            item["name"]
            for item in inspector.get_check_constraints(
                "memory_projection_outbox"
            )
        }
        self.assertIn("ck_outbox_status", checks)

    def test_schema_table_names_match_sqlite_contract(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            sqlite_engine = create_database_engine(
                f"sqlite:///{(Path(temporary) / 'tables.db').as_posix()}"
            )
            try:
                migrate(sqlite_engine)
                sqlite_tables = set(inspect(sqlite_engine).get_table_names())
            finally:
                sqlite_engine.dispose()
        postgres_tables = set(inspect(self.engine).get_table_names())
        self.assertEqual(sqlite_tables, postgres_tables)


if __name__ == "__main__":
    unittest.main()
