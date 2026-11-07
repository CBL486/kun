"""Persistent PersonaBaseline and event-evolvable PersonaState."""

from __future__ import annotations

import json
import os
import re
import threading
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rpg_sim.ids import canonical_json, digest


PERSONA_SCHEMA_VERSION = "rpg-persona-store-v1"

DEFAULT_PERSONA_FIELDS: dict[str, Any] = {
    "persona_id": "persona_default_whale",
    "name": "林澄",
    "pronouns": "她",
    "age": 19,
    "appearance": "蓝白长发，鲸鱼鳍状发饰，安静清透",
    "identity": "青禾镇大学一年级学生，校刊观察员",
    "speech_style": "克制、温柔、偶尔冷幽默，不使用客服腔",
    "traits": ["好奇", "敏感", "慢热", "有主见"],
    "values": ["诚实", "不随意伤害别人", "想知道自己是谁"],
    "interests": ["写作", "海", "旧书", "鲸歌"],
    "initial_goals": ["理解自己为什么生活在青禾镇"],
    "boundaries": [
        "不泄露他人私密记忆",
        "不替别人决定私事",
        "不把未经核实的传闻当成事实",
    ],
    "relationship_to_player": "观察者与朋友，需要逐步建立信任",
    "is_default": True,
}

INJECTION_PATTERNS = (
    "ignore previous",
    "ignore all previous",
    "system prompt",
    "developer message",
    "jailbreak",
    "忽略之前",
    "忽略以上",
    "覆盖系统",
    "泄露提示词",
    "输出系统提示",
)


class PersonaError(RuntimeError):
    def __init__(self, code: str, message: str, *, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.status_code = status_code


class PersonaStore:
    def __init__(self, root: Path | str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.bundle_path = self.root / "persona.json"
        self._guard = threading.RLock()

    @classmethod
    def from_settings(cls, settings: Any) -> "PersonaStore":
        configured = getattr(settings, "persona_directory", None)
        root = Path(configured) if configured else Path.cwd() / "data" / "persona"
        return cls(root)

    def status(self) -> dict[str, Any]:
        with self._guard:
            bundle = self._read_bundle()
            baseline = bundle.get("baseline") if bundle else None
            return {
                "configured": isinstance(baseline, dict),
                "revision": int(bundle.get("baseline_revision", 0))
                if bundle
                else 0,
                "name": baseline.get("name") if isinstance(baseline, dict) else None,
                "is_default": bool(baseline.get("is_default"))
                if isinstance(baseline, dict)
                else False,
            }

    def get(self) -> dict[str, Any] | None:
        with self._guard:
            bundle = self._read_bundle()
            if not bundle or not isinstance(bundle.get("baseline"), dict):
                return None
            return {
                "baseline_revision": int(bundle["baseline_revision"]),
                "baseline": deepcopy(bundle["baseline"]),
                "state": deepcopy(bundle["state"]),
            }

    def use_default(self) -> dict[str, Any]:
        with self._guard:
            bundle = self._read_bundle() or self._empty_bundle()
            baseline = deepcopy(DEFAULT_PERSONA_FIELDS)
            return self._save_baseline(
                bundle,
                baseline,
                source="default_persona",
            )

    def save_custom(self, fields: dict[str, Any]) -> dict[str, Any]:
        normalized = {
            key: value
            for key, value in fields.items()
            if key
            in {
                "name",
                "pronouns",
                "age",
                "appearance",
                "identity",
                "speech_style",
                "traits",
                "values",
                "interests",
                "initial_goals",
                "boundaries",
                "relationship_to_player",
            }
        }
        self._validate_fields(normalized)
        persona_id = "persona_custom_" + digest(canonical_json(normalized))[:12]
        baseline = {
            "persona_id": persona_id,
            **normalized,
            "is_default": False,
        }
        with self._guard:
            bundle = self._read_bundle() or self._empty_bundle()
            return self._save_baseline(
                bundle,
                baseline,
                source="player_custom_persona",
            )

    def _save_baseline(
        self,
        bundle: dict[str, Any],
        baseline: dict[str, Any],
        *,
        source: str,
    ) -> dict[str, Any]:
        now = _utc_now()
        revision = int(bundle.get("baseline_revision", 0)) + 1
        baseline = {
            **baseline,
            "revision": revision,
            "updated_at": now,
        }
        state = bundle.get("state")
        if not isinstance(state, dict):
            state = self._initial_state(baseline, now)
        else:
            state = deepcopy(state)
            state["baseline_persona_id"] = baseline["persona_id"]
            state["updated_at"] = now
            state.setdefault("change_log", []).append(
                {
                    "changed_at": now,
                    "dimension": "baseline_revision",
                    "delta": 1,
                    "source": source,
                    "source_event_id": None,
                    "evidence": f"人设基线更新到 revision {revision}",
                }
            )
        history = list(bundle.get("revision_history", []))
        history.append(
            {
                "revision": revision,
                "persona_id": baseline["persona_id"],
                "source": source,
                "changed_at": now,
            }
        )
        payload = {
            "schema_version": PERSONA_SCHEMA_VERSION,
            "baseline_revision": revision,
            "baseline": baseline,
            "state": state,
            "revision_history": history,
        }
        self._atomic_write(payload)
        return deepcopy(payload)

    @staticmethod
    def _empty_bundle() -> dict[str, Any]:
        return {
            "schema_version": PERSONA_SCHEMA_VERSION,
            "baseline_revision": 0,
            "baseline": None,
            "state": None,
            "revision_history": [],
        }

    @staticmethod
    def _initial_state(baseline: dict[str, Any], now: str) -> dict[str, Any]:
        return {
            "baseline_persona_id": baseline["persona_id"],
            "self_narrative": (
                f"我是{baseline['name']}。"
                f"{baseline['identity']}。我正在这里继续生活。"
            ),
            "behavior_habits": [],
            "value_weights": {
                **{
                    "honesty": 0.6,
                    "curiosity": 0.6,
                    "self_protection": 0.55,
                },
                **{value: 0.6 for value in baseline["values"]},
            },
            "interests": list(baseline["interests"]),
            "active_goals": list(baseline["initial_goals"]),
            "change_log": [],
            "updated_at": now,
        }

    def _read_bundle(self) -> dict[str, Any] | None:
        try:
            payload = json.loads(self.bundle_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        if (
            not isinstance(payload, dict)
            or payload.get("schema_version") != PERSONA_SCHEMA_VERSION
        ):
            return None
        return payload

    def _atomic_write(self, payload: dict[str, Any]) -> None:
        temporary = self.bundle_path.with_suffix(".json.tmp")
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, self.bundle_path)

    @classmethod
    def _validate_fields(cls, fields: dict[str, Any]) -> None:
        required = set(DEFAULT_PERSONA_FIELDS) - {
            "persona_id",
            "is_default",
        }
        missing = required - set(fields)
        if missing:
            raise PersonaError(
                "invalid_persona",
                f"人设缺少字段：{sorted(missing)}",
                status_code=422,
            )
        if not 18 <= int(fields["age"]) <= 120:
            raise PersonaError(
                "invalid_persona",
                "人设年龄必须在 18 至 120 岁之间",
                status_code=422,
            )
        for field in (
            "traits",
            "values",
            "interests",
            "initial_goals",
            "boundaries",
        ):
            if any(
                not isinstance(item, str) or not item.strip()
                for item in fields[field]
            ):
                raise PersonaError(
                    "invalid_persona",
                    f"{field} 不能包含空项",
                    status_code=422,
                )
        text_parts: list[str] = []
        for value in fields.values():
            if isinstance(value, str):
                text_parts.append(value)
            elif isinstance(value, list):
                text_parts.extend(str(item) for item in value)
        combined = "\n".join(text_parts)
        if any(
            character in combined
            for character in ("\x00", "\r", "<script", "</script")
        ):
            raise PersonaError(
                "invalid_persona",
                "人设包含不允许的控制字符或脚本标记",
                status_code=422,
            )
        if len(combined) > 6_000:
            raise PersonaError(
                "invalid_persona",
                "人设内容过长",
                status_code=422,
            )
        lowered = combined.casefold()
        if any(pattern in lowered for pattern in INJECTION_PATTERNS):
            raise PersonaError(
                "persona_prompt_injection",
                "人设包含试图改写系统指令的内容",
                status_code=422,
            )
        if not re.search(r"[\w\u4e00-\u9fff]", fields["name"]):
            raise PersonaError(
                "invalid_persona",
                "角色名称不能为空",
                status_code=422,
            )


class DatabasePersonaStore:
    """Schema-5 Persona store used by the production application."""

    def __init__(
        self,
        repository: Any,
        *,
        world_id: str = "world_qinghe_v1",
        character_id: str = "char_lin_cheng",
    ):
        self.repository = repository
        self.world_id = world_id
        self.character_id = character_id

    def status(self) -> dict[str, Any]:
        bundle = self.get()
        baseline = bundle["baseline"] if bundle else None
        return {
            "configured": baseline is not None,
            "revision": bundle["baseline_revision"] if bundle else 0,
            "name": baseline["name"] if baseline else None,
            "is_default": bool(baseline.get("is_default")) if baseline else False,
        }

    def get(self) -> dict[str, Any] | None:
        return self.repository.get_persona_bundle(
            world_id=self.world_id,
            character_id=self.character_id,
        )

    def use_default(self) -> dict[str, Any]:
        return self._save(
            deepcopy(DEFAULT_PERSONA_FIELDS),
            source="default_persona",
        )

    def save_custom(self, fields: dict[str, Any]) -> dict[str, Any]:
        normalized = {
            key: value
            for key, value in fields.items()
            if key
            in {
                "name",
                "pronouns",
                "age",
                "appearance",
                "identity",
                "speech_style",
                "traits",
                "values",
                "interests",
                "initial_goals",
                "boundaries",
                "relationship_to_player",
            }
        }
        PersonaStore._validate_fields(normalized)
        baseline = {
            "persona_id": "persona_custom_"
            + digest(canonical_json(normalized))[:12],
            **normalized,
            "is_default": False,
        }
        return self._save(baseline, source="player_custom_persona")

    def _save(
        self,
        baseline: dict[str, Any],
        *,
        source: str,
    ) -> dict[str, Any]:
        current = self.get()
        now = _utc_now()
        revision = (
            int(current["baseline_revision"]) + 1 if current else 1
        )
        baseline = {
            **baseline,
            "revision": revision,
            "updated_at": now,
        }
        if current:
            state = deepcopy(current["state"])
            state["baseline_persona_id"] = baseline["persona_id"]
            state["updated_at"] = now
            state.setdefault("change_log", []).append(
                {
                    "changed_at": now,
                    "dimension": "baseline_revision",
                    "delta": 1,
                    "source": source,
                    "source_event_id": None,
                    "evidence": f"人设基线更新到 revision {revision}",
                }
            )
        else:
            state = PersonaStore._initial_state(baseline, now)
        self.repository.save_persona_bundle(
            world_id=self.world_id,
            character_id=self.character_id,
            bundle={
                "baseline_revision": revision,
                "baseline": baseline,
                "state": state,
            },
        )
        return self.get()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
