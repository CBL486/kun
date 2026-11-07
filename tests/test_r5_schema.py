from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import inspect, select
from sqlalchemy.orm import Session

from app.persona import DatabasePersonaStore, PersonaStore
from app.persona import DEFAULT_PERSONA_FIELDS
from app.persona_policy import SYSTEM_PERSONA_SAFETY_POLICY
from app.setup import DeepSeekSetupStore
from rpg_orm.migrations import (
    LATEST_SCHEMA_VERSION,
    create_database_engine,
    migrate,
    schema_version,
)
from rpg_orm.models import (
    DeepSeekCredentialRow,
    PersonaBaselineRow,
    PersonaChangeLogRow,
    SchemaVersionRow,
    SetupStateRow,
)
from rpg_orm.product_repository import ProductRepository
from rpg_storage.errors import StorageError

WORLD_ID = "world_qinghe_v1"
CHARACTER_ID = "char_lin_cheng"

try:
    import pgserver
    import pgserver.postgres_server as pgserver_module
    from pgserver._commands import POSTGRES_BIN_PATH

    PG_SERVER_AVAILABLE = True
except ImportError:
    PG_SERVER_AVAILABLE = False


def engine_for(tmp_path: Path):
    return create_database_engine(
        f"sqlite:///{(tmp_path / 'schema5.db').as_posix()}"
    )


def event_payload() -> dict:
    return {
        "event_id": "evt_r5_event_001",
        "world_id": WORLD_ID,
        "actor_id": CHARACTER_ID,
        "participants": [CHARACTER_ID],
        "location_id": "loc_library",
        "event_type": "conversation_completed",
        "occurred_at": "2026-11-07T10:00:00+08:00",
        "summary": "林澄认真听完了一段往事。",
        "valence": 0.3,
        "intensity": 0.5,
        "importance": 0.7,
        "confidence": 0.98,
        "visibility": "private",
        "source": "player",
        "dedupe_key": "r5:event:001",
        "metadata": {"channel": "chat"},
    }


def test_schema_five_adds_product_tables_and_migrates_version_four(tmp_path) -> None:
    engine = engine_for(tmp_path)
    try:
        assert migrate(engine) == LATEST_SCHEMA_VERSION == 5
        tables = set(inspect(engine).get_table_names())
        assert {
            "memory_events",
            "relationship_states",
            "emotion_states",
            "persona_baselines",
            "persona_states",
            "persona_change_log",
            "study_sessions",
            "media_observations",
            "setup_state",
            "deepseek_credentials",
            "world_clock_states",
        } <= tables
        credential_columns = {
            column["name"]
            for column in inspect(engine).get_columns("deepseek_credentials")
        }
        assert "key_ref" in credential_columns
        assert "api_key" not in credential_columns
        with Session(engine) as session, session.begin():
            session.add(
                SchemaVersionRow(
                    version=4,
                    applied_at="2026-11-01T00:00:00+00:00",
                )
            )
        assert migrate(engine) == 5
    finally:
        engine.dispose()


def test_event_relationship_and_emotion_require_event_evidence(tmp_path) -> None:
    engine = engine_for(tmp_path)
    repository = ProductRepository(engine)
    try:
        with pytest.raises(StorageError) as caught:
            repository.apply_relationship(
                event_id="evt_missing",
                relationship_id="rel_lin_player",
                world_id=WORLD_ID,
                from_character_id=CHARACTER_ID,
                to_character_id="observer_demo_001",
                deltas={"trust": 0.1},
                updated_at="2026-11-07T10:01:00+08:00",
            )
        assert caught.value.code == "unknown_event"

        event = repository.record_memory_event(event_payload())
        replay = repository.record_memory_event(event_payload())
        assert replay["event_id"] == event["event_id"]

        relationship = repository.apply_relationship(
            event_id=event["event_id"],
            relationship_id="rel_lin_player",
            world_id=WORLD_ID,
            from_character_id=CHARACTER_ID,
            to_character_id="observer_demo_001",
            deltas={"trust": 0.1, "familiarity": 0.05},
            updated_at="2026-11-07T10:01:00+08:00",
        )
        replay_relationship = repository.apply_relationship(
            event_id=event["event_id"],
            relationship_id="rel_lin_player",
            world_id=WORLD_ID,
            from_character_id=CHARACTER_ID,
            to_character_id="observer_demo_001",
            deltas={"trust": 0.1, "familiarity": 0.05},
            updated_at="2026-11-07T10:01:00+08:00",
        )
        assert replay_relationship == relationship
        assert relationship["last_event_id"] == event["event_id"]

        emotion = repository.update_emotion(
            event_id=event["event_id"],
            world_id=WORLD_ID,
            character_id=CHARACTER_ID,
            values={"valence": 0.4},
            updated_at="2026-11-07T10:01:00+08:00",
        )
        assert emotion["valence"] == 0.4
        assert emotion["last_event_id"] == event["event_id"]
    finally:
        engine.dispose()


def test_persona_safety_boundaries_live_outside_user_baseline() -> None:
    baseline_text = "\n".join(DEFAULT_PERSONA_FIELDS["boundaries"])
    policy_text = "\n".join(SYSTEM_PERSONA_SAFETY_POLICY.values())
    assert "现实身体" not in baseline_text
    assert "现实联系方式" not in baseline_text
    assert "现实身体" in policy_text
    assert "现实联系方式" in policy_text
    assert "系统式免责声明" in policy_text


def test_persona_json_migrates_to_schema_five_with_revision_consistency(
    tmp_path,
) -> None:
    persona_root = tmp_path / "persona"
    source = PersonaStore(persona_root)
    source.use_default()
    source.save_custom(
        {
            "name": "潮汐",
            "pronouns": "她",
            "age": 21,
            "appearance": "深海蓝长发与透明鳍饰",
            "identity": "青禾镇夜间图书馆管理员",
            "speech_style": "简洁安静",
            "traits": ["克制", "敏锐"],
            "values": ["诚实", "保护秘密"],
            "interests": ["潮汐记录", "旧地图"],
            "initial_goals": ["整理旧地图"],
            "boundaries": ["不泄露私密记忆"],
            "relationship_to_player": "谨慎的观察者朋友",
        }
    )
    engine = engine_for(tmp_path)
    repository = ProductRepository(engine)
    try:
        migrated = repository.migrate_persona_json(
            persona_root / "persona.json",
            world_id=WORLD_ID,
            character_id=CHARACTER_ID,
        )
        assert migrated["revision"] == 2
        bundle = repository.get_persona_bundle(
            world_id=WORLD_ID,
            character_id=CHARACTER_ID,
        )
        assert bundle["baseline_revision"] == 2
        assert bundle["baseline"]["name"] == "潮汐"
        assert bundle["state"]["baseline_persona_id"].startswith(
            "persona_custom_"
        )
        assert bundle["state"]["change_log"]

        replay = repository.migrate_persona_json(
            persona_root / "persona.json",
            world_id=WORLD_ID,
            character_id=CHARACTER_ID,
        )
        assert replay["revision"] == 2
        with Session(engine) as session:
            baselines = session.scalars(select(PersonaBaselineRow)).all()
            changes = session.scalars(select(PersonaChangeLogRow)).all()
            credentials = session.scalars(select(DeepSeekCredentialRow)).all()
        assert len(baselines) == 1
        assert sum(row.is_active for row in baselines) == 1
        assert changes
        assert credentials == []
    finally:
        engine.dispose()


def test_database_persona_store_replaces_json_runtime(tmp_path) -> None:
    engine = engine_for(tmp_path)
    repository = ProductRepository(engine)
    store = DatabasePersonaStore(
        repository,
        world_id=WORLD_ID,
        character_id=CHARACTER_ID,
    )
    try:
        first = store.use_default()
        assert first["baseline_revision"] == 1
        second = store.save_custom(
            {
                "name": "潮汐",
                "pronouns": "她",
                "age": 21,
                "appearance": "深海蓝长发",
                "identity": "夜间图书馆管理员",
                "speech_style": "简洁安静",
                "traits": ["克制"],
                "values": ["诚实"],
                "interests": ["旧地图"],
                "initial_goals": ["整理旧地图"],
                "boundaries": ["不泄露秘密"],
                "relationship_to_player": "谨慎的观察者朋友",
            }
        )
        assert second["baseline_revision"] == 2
        assert second["baseline"]["name"] == "潮汐"
        assert store.status()["revision"] == 2
        assert store.status()["name"] == "潮汐"
    finally:
        engine.dispose()


def test_product_repository_persists_world_clock(tmp_path) -> None:
    engine = engine_for(tmp_path)
    repository = ProductRepository(engine)
    try:
        first = repository.put_world_clock(
            world_id=WORLD_ID,
            logical_time="2026-11-07T10:00:00+08:00",
            state_revision=51,
            last_tick_at="2026-11-07T10:00:00+08:00",
            catch_up_mode="compressed_catch_up",
            compressed_ticks=2,
            last_summary="压缩补算 2 个 tick。",
            updated_at="2026-11-07T10:00:00+08:00",
        )
        replay = repository.put_world_clock(
            world_id=WORLD_ID,
            logical_time="2026-11-07T10:10:00+08:00",
            state_revision=52,
            last_tick_at="2026-11-07T10:10:00+08:00",
            catch_up_mode="live",
            compressed_ticks=0,
            last_summary=None,
            updated_at="2026-11-07T10:10:00+08:00",
        )
        assert first["state_revision"] == 51
        assert replay["state_revision"] == 52
        assert repository.get_world_clock(WORLD_ID)["compressed_ticks"] == 0
    finally:
        engine.dispose()


def test_setup_json_migrates_references_without_plaintext_key(tmp_path) -> None:
    class FakeValidator:
        def validate(self, api_key: str) -> None:
            assert api_key == "sk-test-r5-setup-ABCD"

    setup_root = tmp_path / "setup"
    setup = DeepSeekSetupStore(setup_root, secure_acl=False)
    setup.save_key("sk-test-r5-setup-ABCD", FakeValidator())
    setup.complete(persona_configured=True)
    engine = engine_for(tmp_path)
    repository = ProductRepository(engine)
    try:
        migrated = repository.migrate_setup_json(setup_root, world_id=WORLD_ID)
        assert migrated["configured"] is True
        assert migrated["world_ready"] is True
        with Session(engine) as session:
            state = session.get(SetupStateRow, WORLD_ID)
            credential = session.scalar(select(DeepSeekCredentialRow))
        assert state.world_ready is True
        assert credential.key_ref == "deepseek_api_key.txt"
        assert credential.key_hint == "sk-...ABCD"
        assert "sk-test-r5-setup" not in json.dumps(
            {
                "key_ref": credential.key_ref,
                "key_hint": credential.key_hint,
            }
        )
    finally:
        engine.dispose()


def _install_windows_safe_pg_commands() -> None:
    def make_command(name: str):
        executable = name if os.name == "nt" else name.removesuffix(".exe")
        encoding = "gbk" if os.name == "nt" else "utf-8"

        def command(args, pgdata=None, **kwargs):
            if pgdata is None:
                raise ValueError("pgdata required")
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
                    [
                        str(POSTGRES_BIN_PATH / executable),
                        "-D",
                        str(pgdata),
                        *args,
                    ],
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
def test_postgres_schema_five_and_product_event(tmp_path) -> None:
    _install_windows_safe_pg_commands()
    server = pgserver.get_server(
        tmp_path / "pgdata",
        cleanup_mode="delete",
    )
    engine = create_database_engine(server.get_uri())
    repository = ProductRepository(engine)
    try:
        assert schema_version(engine) == 5
        event = repository.record_memory_event(event_payload())
        assert event["event_id"] == "evt_r5_event_001"
        tables = set(inspect(engine).get_table_names())
        assert {
            "memory_events",
            "relationship_states",
            "emotion_states",
            "persona_baselines",
            "persona_states",
            "persona_change_log",
            "study_sessions",
            "media_observations",
            "setup_state",
            "deepseek_credentials",
            "world_clock_states",
        } <= tables
    finally:
        engine.dispose()
        server.cleanup()
