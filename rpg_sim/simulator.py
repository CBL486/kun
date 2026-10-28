"""七日规则模拟编排、报告与快照。"""

from __future__ import annotations

import copy
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .budget import BudgetExceeded, DailyBudget
from .engine import WorldEngine
from .ids import canonical_json, digest, relationship_id, stable_id
from .mocks import MockLLM, MockReviewer
from .scenario import (
    ACTIONS,
    CODE_VERSION,
    CRITICAL_TEMPLATES,
    DAILY_ROUTES,
    DIRECTOR_TEMPLATES,
    END_TIME,
    MAIN_ID,
    OBSERVER_ID,
    SCENARIO_ID,
    SEED,
    SHARE_EXPECTED_TEMPLATES,
    SHARE_TIME,
    START_TIME,
    TEMPLATE_REGISTRY_VERSION,
    TIMEZONE,
    WORLD_ID,
    candidate_id,
    initial_world,
)


class SimulationError(RuntimeError):
    pass


CHECKPOINT_VERSION = "rpg-sim-checkpoint-v1"


@dataclass
class SimulationResult:
    report: dict[str, Any]
    snapshot_before: dict[str, Any]
    snapshot_after: dict[str, Any]
    complete: bool = True


class SevenDaySimulator:
    def __init__(
        self,
        *,
        scenario_id: str = SCENARIO_ID,
        seed: int = SEED,
        mode: str = "rule_only",
        frozen_clock: bool = True,
        checkpoint_path: Path | str | None = None,
        resume: bool = False,
        pause_after_steps: int | None = None,
    ):
        if scenario_id != SCENARIO_ID:
            raise SimulationError(f"未知场景：{scenario_id}")
        if seed != SEED:
            raise SimulationError(f"B1 只接受冻结 seed={SEED}")
        if mode != "rule_only":
            raise SimulationError("B1 首轮只实现 rule_only，拒绝网络模型模式")
        if not frozen_clock:
            raise SimulationError("B1 必须使用 --frozen-clock")

        self.scenario_id = scenario_id
        self.seed = seed
        self.mode = mode
        self.checkpoint_path = Path(checkpoint_path).resolve() if checkpoint_path else None
        self.pause_after_steps = pause_after_steps
        self._run_steps = 0
        self.engine = WorldEngine(initial_world())
        self.llm = MockLLM(seed)
        self.reviewer = MockReviewer()
        self.memories: list[dict[str, Any]] = []
        self.memory_write_records: list[dict[str, Any]] = []
        self.memory_read_explanations: list[dict[str, Any]] = []
        self.action_attempts: list[dict[str, Any]] = []
        self.typed_rejections: list[dict[str, Any]] = []
        self.director_candidates: list[dict[str, Any]] = []
        self.director_rejected_candidates: list[dict[str, Any]] = []
        self.daily_shares: list[dict[str, Any]] = []
        self.diary_records: list[dict[str, Any]] = []
        self.npc_reaction_records: list[dict[str, Any]] = []
        self.relationship_changes: list[dict[str, Any]] = []
        self.budgets: dict[str, DailyBudget] = {}
        self.degradation_events: list[dict[str, Any]] = []
        self.fault_cases: list[dict[str, Any]] = []
        self._budget_failures: list[dict[str, Any]] = []
        self._pending_activity_id: str | None = None
        self._initial_snapshot = self.engine.snapshot()
        self._progress: dict[str, Any] = {
            "day_index": 0,
            "phase": "day_start",
            "cursor": 0,
            "complete": False,
        }
        if resume:
            if not self.checkpoint_path or not self.checkpoint_path.is_file():
                raise SimulationError("恢复模式要求存在 checkpoint.json")
            self._restore_checkpoint(self.checkpoint_path)

    @classmethod
    def from_checkpoint(
        cls,
        checkpoint_path: Path | str,
        *,
        pause_after_steps: int | None = None,
    ) -> "SevenDaySimulator":
        return cls(
            checkpoint_path=checkpoint_path,
            resume=True,
            pause_after_steps=pause_after_steps,
        )

    def run(self) -> SimulationResult:
        self._run_steps = 0
        while not self._progress["complete"]:
            day_items = list(DAILY_ROUTES.items())
            day_index = self._progress["day_index"]
            if day_index >= len(day_items):
                self._progress = {
                    "day_index": len(day_items),
                    "phase": "complete",
                    "cursor": 0,
                    "complete": True,
                }
                self._save_checkpoint()
                break
            world_date, route = day_items[day_index]
            if self._progress["phase"] == "day_start":
                self._start_day(day_index, world_date)
                self._progress = {
                    "day_index": day_index,
                    "phase": "pre_share",
                    "cursor": 0,
                    "complete": False,
                }
                self._save_checkpoint()

            if self._progress["phase"] == "pre_share":
                while True:
                    next_index = self._next_route_index(
                        route,
                        self._progress["cursor"],
                        before_share=True,
                    )
                    if next_index is None:
                        break
                    self._run_step(world_date, next_index, route[next_index])
                    self._progress["cursor"] = next_index + 1
                    self._save_checkpoint()
                    if self._pause_requested():
                        return self._paused_result()
                self.engine.settle_evening(world_date)
                self._create_daily_share(world_date)
                self._progress["phase"] = "post_share"
                self._progress["cursor"] = 0
                self._save_checkpoint()

            if self._progress["phase"] == "post_share":
                while True:
                    next_index = self._next_route_index(
                        route,
                        self._progress["cursor"],
                        before_share=False,
                    )
                    if next_index is None:
                        break
                    self._run_step(world_date, next_index, route[next_index])
                    self._progress["cursor"] = next_index + 1
                    self._save_checkpoint()
                    if self._pause_requested():
                        return self._paused_result()
                self._record_rejected_candidates(world_date)
                self._progress = {
                    "day_index": day_index + 1,
                    "phase": "day_start",
                    "cursor": 0,
                    "complete": False,
                }
                self._save_checkpoint()

        snapshot_after = self.engine.snapshot()
        report = self._build_report(self._initial_snapshot, snapshot_after)
        report["status"] = "completed"
        report["checkpoint"] = {
            "version": CHECKPOINT_VERSION,
            "path": str(self.checkpoint_path) if self.checkpoint_path else None,
        }
        return SimulationResult(
            report=report,
            snapshot_before=self._initial_snapshot,
            snapshot_after=snapshot_after,
            complete=True,
        )

    def _start_day(self, day_index: int, world_date: str) -> None:
        if world_date in self.budgets:
            return
        self.budgets[world_date] = DailyBudget(world_date)
        self._generate_director_candidates(day_index, world_date)
        self._recall_for_sunday(world_date)

    @staticmethod
    def _next_route_index(
        route: list[dict[str, Any]],
        cursor: int,
        *,
        before_share: bool,
    ) -> int | None:
        for index in range(cursor, len(route)):
            is_before_share = route[index]["time"] < SHARE_TIME
            if is_before_share == before_share:
                return index
        return None

    def _pause_requested(self) -> bool:
        self._run_steps += 1
        return (
            self.pause_after_steps is not None
            and self._run_steps >= self.pause_after_steps
        )

    def _paused_result(self) -> SimulationResult:
        snapshot = self.engine.snapshot()
        report = {
            "status": "paused",
            "scenario_id": self.scenario_id,
            "seed": self.seed,
            "clock_mode": "frozen",
            "code_version": CODE_VERSION,
            "progress": copy.deepcopy(self._progress),
            "committed_event_count": len(self.engine.state["events"]),
            "snapshot_before": digest(self._initial_snapshot),
            "snapshot_current": digest(snapshot),
            "checkpoint": {
                "version": CHECKPOINT_VERSION,
                "path": str(self.checkpoint_path) if self.checkpoint_path else None,
            },
        }
        return SimulationResult(
            report=report,
            snapshot_before=self._initial_snapshot,
            snapshot_after=snapshot,
            complete=False,
        )

    def _checkpoint_payload(self) -> dict[str, Any]:
        return {
            "schema_version": CHECKPOINT_VERSION,
            "scenario_id": self.scenario_id,
            "seed": self.seed,
            "mode": self.mode,
            "progress": copy.deepcopy(self._progress),
            "initial_snapshot": copy.deepcopy(self._initial_snapshot),
            "engine_state": self.engine.snapshot(),
            "engine_operations": copy.deepcopy(self.engine.operations),
            "memories": copy.deepcopy(self.memories),
            "memory_write_records": copy.deepcopy(self.memory_write_records),
            "memory_read_explanations": copy.deepcopy(self.memory_read_explanations),
            "action_attempts": copy.deepcopy(self.action_attempts),
            "typed_rejections": copy.deepcopy(self.typed_rejections),
            "director_candidates": copy.deepcopy(self.director_candidates),
            "director_rejected_candidates": copy.deepcopy(
                self.director_rejected_candidates
            ),
            "daily_shares": copy.deepcopy(self.daily_shares),
            "diary_records": copy.deepcopy(self.diary_records),
            "npc_reaction_records": copy.deepcopy(self.npc_reaction_records),
            "relationship_changes": copy.deepcopy(self.relationship_changes),
            "budgets": {
                world_date: budget.to_dict()
                for world_date, budget in self.budgets.items()
            },
            "degradation_events": copy.deepcopy(self.degradation_events),
            "fault_cases": copy.deepcopy(self.fault_cases),
            "budget_failures": copy.deepcopy(self._budget_failures),
            "pending_activity_id": self._pending_activity_id,
        }

    def _save_checkpoint(self) -> None:
        if not self.checkpoint_path:
            return
        self.checkpoint_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.checkpoint_path.with_suffix(
            self.checkpoint_path.suffix + ".tmp"
        )
        temporary.write_text(
            json.dumps(
                self._checkpoint_payload(),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, self.checkpoint_path)

    def _restore_checkpoint(self, path: Path) -> None:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise SimulationError(f"检查点不可读取：{error}") from error
        if payload.get("schema_version") != CHECKPOINT_VERSION:
            raise SimulationError("检查点版本不兼容")
        if payload.get("scenario_id") != self.scenario_id or payload.get("seed") != self.seed:
            raise SimulationError("检查点与场景或 seed 不匹配")
        self.mode = payload["mode"]
        self.engine = WorldEngine(payload["engine_state"])
        self.engine.operations = copy.deepcopy(payload["engine_operations"])
        self.memories = payload["memories"]
        self.memory_write_records = payload["memory_write_records"]
        self.memory_read_explanations = payload["memory_read_explanations"]
        self.action_attempts = payload["action_attempts"]
        self.typed_rejections = payload["typed_rejections"]
        self.director_candidates = payload["director_candidates"]
        self.director_rejected_candidates = payload[
            "director_rejected_candidates"
        ]
        self.daily_shares = payload["daily_shares"]
        self.diary_records = payload["diary_records"]
        self.npc_reaction_records = payload["npc_reaction_records"]
        self.relationship_changes = payload["relationship_changes"]
        self.budgets = {}
        for world_date, source in payload["budgets"].items():
            self.budgets[world_date] = DailyBudget(
                world_date=world_date,
                world_events=source["world_events"],
                shares=source["shares"],
                journals=source["journals"],
                model_calls=source["model_calls"],
                review_calls=source["review_calls"],
                input_tokens=source["input_tokens"],
                output_tokens=source["output_tokens"],
                cost_cny=source["cost_cny"],
            )
        self.degradation_events = payload["degradation_events"]
        self.fault_cases = payload["fault_cases"]
        self._budget_failures = payload["budget_failures"]
        self._pending_activity_id = payload["pending_activity_id"]
        self._progress = payload["progress"]
        self._initial_snapshot = payload["initial_snapshot"]

    def _run_step(
        self,
        world_date: str,
        ordinal: int,
        step: dict[str, Any],
    ) -> None:
        action_type = step["action_type"]
        budget = self.budgets[world_date]
        can_commit, metric = budget.can_commit_event(action_type)
        if not can_commit:
            self._budget_failures.append(
                {
                    "world_date": world_date,
                    "metric": metric,
                    "action_type": action_type,
                }
            )
            self.degradation_events.append(
                {
                    "world_date": world_date,
                    "code": "budget_exceeded",
                    "metric": metric,
                    "handling": "规则模式继续，但不提交超出预算的事件",
                }
            )
            return

        self.engine.prepare_time(world_date, step["time"], step["slot"])
        tick_id = stable_id(
            "tick",
            [
                WORLD_ID,
                MAIN_ID,
                world_date,
                step["slot"],
                f"{world_date}:{step['slot']}",
            ],
        )
        operation_id = f"op_{world_date.replace('-', '')}_lin_{ordinal + 1:02}"
        nonce = digest({"operation_id": operation_id})[:16]
        action_id = stable_id("act", [tick_id, ordinal, nonce])
        candidate = self._candidate_for_template(step.get("template_id"))
        intent = {
            "action_id": action_id,
            "operation_id": operation_id,
            "tick_id": tick_id,
            "world_id": WORLD_ID,
            "character_id": MAIN_ID,
            "action_type": action_type,
            "target_id": step["target_id"],
            "parameters": copy.deepcopy(step["parameters"]),
            "expected_state_version": self.engine.state["state_version"],
            "origin": "rule_engine",
            "intent_nonce": nonce,
        }
        if candidate:
            intent["source_candidate_id"] = candidate["candidate_id"]
        result = self.engine.apply(
            intent,
            event_template_id=step.get("template_id"),
        )
        attempt = {
            "world_date": world_date,
            "slot_key": step["slot"],
            "logical_time": self.engine.state["logical_time"],
            "tick_id": tick_id,
            "operation_id": operation_id,
            "action_id": action_id,
            "action_type": action_type,
            "target_id": step["target_id"],
            "status": "accepted" if result["ok"] else "rejected",
            "event_id": result["event"]["event_id"] if result["event"] else None,
            "error_code": result["code"],
            "replayed": result["replayed"],
            "model_used": False,
            "mode": self.mode,
        }
        self.action_attempts.append(attempt)
        if not result["ok"]:
            rejection = {
                "world_date": world_date,
                "operation_id": operation_id,
                "action_id": action_id,
                "code": result["code"],
                "safe_message": result["message"],
            }
            self.typed_rejections.append(rejection)
            try:
                budget.discard_failed_attempt()
            except BudgetExceeded as error:
                self._handle_budget_exception(world_date, error)
            return

        event = result["event"]
        if result["replayed"]:
            return

        try:
            budget.record_event(
                action_type,
                visible=event["visibility"] != "internal",
            )
        except BudgetExceeded as error:
            # 提交前已检查，这里只记录不可达的防御性失败。
            self._handle_budget_exception(world_date, error)
            return

        if candidate:
            candidate["consumed_by_action_id"] = action_id
            candidate["event_id"] = event["event_id"]
        self._record_event_memory(event)
        self.relationship_changes.extend(copy.deepcopy(event["relationship_changes"]))
        if action_type == "talk":
            self._record_npc_reaction(event)
        if action_type == "write_journal":
            self.diary_records.append(
                {
                    "diary_id": stable_id(
                        "diary", [event["event_id"], MAIN_ID, "journal"]
                    ),
                    "event_id": event["event_id"],
                    "world_date": world_date,
                    "created_at": event["committed_at"],
                    "trigger_id": step["parameters"]["trigger_id"],
                    "visibility": "internal",
                    "summary": event["summary"],
                }
            )

    def _record_event_memory(self, event: dict[str, Any]) -> None:
        candidate = event["memory_candidates"][0]
        dedupe_key = (
            f"rpg:{event['event_id']}:{MAIN_ID}:{candidate['candidate_index']}"
        )
        if any(memory["dedupe_key"] == dedupe_key for memory in self.memories):
            return
        memory_id = stable_id(
            "mem",
            [
                event["event_id"],
                MAIN_ID,
                candidate["candidate_index"],
                dedupe_key,
            ],
        )
        memory = {
            "memory_id": memory_id,
            "scope": {
                "tenant_id": "rpg-world",
                "world_id": WORLD_ID,
                "user_id": OBSERVER_ID,
                "character_id": MAIN_ID,
                "surface": "school",
                "conversation_id": (
                    None
                    if event["event_type"] == "journal_written"
                    else f"day-{event['world_date']}"
                ),
            },
            "kind": candidate["kind"],
            "source": candidate["source"],
            "content": candidate["summary"],
            "source_event_id": event["event_id"],
            "world_date": event["world_date"],
            "importance": candidate["importance"],
            "emotional_weight": candidate["emotional_weight"],
            "confidence": 0.98,
            "strength": round(0.45 + candidate["importance"] * 0.35, 4),
            "scene_tags": candidate["scene_tags"],
            "created_at": event["committed_at"],
            "locked": False,
            "state": "active",
            "dedupe_key": dedupe_key,
        }
        self.memories.append(memory)
        self.memory_write_records.append(
            {
                "memory_id": memory_id,
                "source_event_id": event["event_id"],
                "dedupe_key": dedupe_key,
                "status": "written",
            }
        )

    def _record_npc_reaction(self, event: dict[str, Any]) -> None:
        npc_id = next(
            participant for participant in event["participants"] if participant.startswith("npc_")
        )
        reactions = {
            "npc_gao": "先吃饭，别把事儿饿坏了。菜单就这些，其他的我没听说。",
            "npc_su": "这版先做出来再说；不过重点要不要保留，我们得说清楚。",
            "npc_chen": "先把事实说清楚。提交楼层以公开通知为准。",
            "npc_gu": "我只看见镜头里的这一面。用途和范围先说明白。",
        }
        reaction = {
            "schema_version": "rpg-npc-reaction-v1",
            "npc_id": npc_id,
            "response_to_event_id": event["event_id"],
            "template_id": f"say_{npc_id[4:]}_{event['template_id']}",
            "utterance": reactions[npc_id],
            "knowledge_basis": event["knowledge_basis"],
            "review_status": "approved",
            "model_used": False,
        }
        if not any(
            item["response_to_event_id"] == event["event_id"]
            and item["npc_id"] == npc_id
            for item in self.npc_reaction_records
        ):
            self.npc_reaction_records.append(reaction)

    def _generate_director_candidates(self, day_index: int, world_date: str) -> None:
        templates = [
            (template_id, template)
            for template_id, template in DIRECTOR_TEMPLATES.items()
            if template["day"] == world_date
        ][:5]
        first_step = DAILY_ROUTES[world_date][0]
        tick_id = stable_id(
            "tick",
            [
                WORLD_ID,
                MAIN_ID,
                world_date,
                first_step["slot"],
                f"{world_date}:{first_step['slot']}",
            ],
        )
        for index, (template_id, template) in enumerate(templates):
            source_seq = day_index * 10 + index
            cid = candidate_id(WORLD_ID, tick_id, template_id, source_seq)
            jitter = (int(digest([SEED, template_id])[:4], 16) % 7) / 100
            candidate = {
                "schema_version": "rpg-director-candidate-v1",
                "candidate_id": cid,
                "template_id": template_id,
                "world_id": WORLD_ID,
                "tick_id": tick_id,
                "world_date": world_date,
                "slot_key": first_step["slot"],
                "event_kind": template["kind"],
                "location_id": template["locations"][0],
                "participant_ids": template["participants"],
                "priority": round(0.68 + jitter, 2),
                "preconditions": ["registered_template", "date_window_matches"],
                "constraints": {
                    "max_uses_per_world_day": 1,
                    "max_global_uses": 1,
                    "forbidden_topics": ["romance", "trade", "violence"],
                },
                "visible_hint": template["hint"],
                "visibility": "user_visible",
                "state_write": None,
                "review_status": "approved",
                "consumed_by_action_id": None,
                "event_id": None,
            }
            self.director_candidates.append(candidate)

    def _candidate_for_template(self, template_id: str | None) -> dict[str, Any] | None:
        if not template_id:
            return None
        matches = [
            candidate
            for candidate in self.director_candidates
            if candidate["template_id"] == template_id
            and candidate["event_id"] is None
            and candidate["world_date"] == self.engine.state["world_date"]
        ]
        return matches[0] if matches else None

    def _record_rejected_candidates(self, world_date: str) -> None:
        for candidate in self.director_candidates:
            if candidate["world_date"] != world_date or candidate["event_id"] is not None:
                continue
            self.director_rejected_candidates.append(
                {
                    "candidate_id": candidate["candidate_id"],
                    "template_id": candidate["template_id"],
                    "world_date": world_date,
                    "code": "not_selected",
                    "safe_message": "候选未进入本次固定决策路线",
                }
            )

    def _create_daily_share(self, world_date: str) -> None:
        visible = [
            event
            for event in self.engine.state["events"]
            if event["world_date"] == world_date
            and event["visibility"] == "user_visible"
        ][:5]
        if len(visible) < 3:
            raise SimulationError(f"{world_date} 可分享公开事件少于 3 件")
        source_ids = [event["event_id"] for event in visible]
        summaries = [event["summary"] for event in visible]
        share_id = stable_id("share", [world_date, MAIN_ID, *source_ids])
        generated = self.llm.complete(
            "daily_share",
            {"world_date": world_date, "summaries": summaries},
        )
        review_status = self.reviewer.review(generated.text)
        if review_status != "approved":
            raise SimulationError(f"{world_date} 分享内容审核未通过")
        share = {
            "share_id": share_id,
            "world_date": world_date,
            "character_id": MAIN_ID,
            "created_at": f"{world_date}T{SHARE_TIME}:00+08:00",
            "source_event_ids": source_ids,
            "layers": generated.text,
            "review_status": review_status,
            "provider": generated.provider,
        }
        self.daily_shares.append(share)
        try:
            self.budgets[world_date].record_share(
                input_tokens=generated.input_tokens,
                output_tokens=generated.output_tokens,
            )
        except BudgetExceeded as error:
            self._handle_budget_exception(world_date, error)
            return

        dedupe_key = f"rpg:share:{world_date}:{MAIN_ID}:0"
        memory_id = stable_id("mem", [share_id, MAIN_ID, dedupe_key])
        if not any(memory["dedupe_key"] == dedupe_key for memory in self.memories):
            memory = {
                "memory_id": memory_id,
                "scope": {
                    "tenant_id": "rpg-world",
                    "world_id": WORLD_ID,
                    "user_id": OBSERVER_ID,
                    "character_id": MAIN_ID,
                    "surface": "school",
                    "conversation_id": f"day-{world_date}",
                },
                "kind": "summary",
                "source": "daily_share",
                "content": share["layers"]["reflection"],
                "source_event_id": source_ids[-1],
                "source_event_ids": source_ids,
                "world_date": world_date,
                "importance": 0.62,
                "emotional_weight": 0.34,
                "confidence": 0.97,
                "strength": 0.70,
                "scene_tags": ["daily_share"],
                "created_at": share["created_at"],
                "locked": False,
                "state": "active",
                "dedupe_key": dedupe_key,
            }
            self.memories.append(memory)
            self.memory_write_records.append(
                {
                    "memory_id": memory_id,
                    "source_event_id": source_ids[-1],
                    "dedupe_key": dedupe_key,
                    "status": "written",
                }
            )

    def _recall_for_sunday(self, world_date: str) -> None:
        if world_date != "2026-11-08":
            return
        wanted_days = ["2026-11-02", "2026-11-04", "2026-11-06"]
        selected = []
        for wanted_day in wanted_days:
            matches = [
                memory
                for memory in self.memories
                if memory["world_date"] == wanted_day
                and memory["kind"] == "event"
                and memory["state"] == "active"
            ]
            if matches:
                selected.append(
                    max(matches, key=lambda item: (item["importance"], item["memory_id"]))
                )
        for memory in selected:
            self.memory_read_explanations.append(
                {
                    "world_date": world_date,
                    "memory_id": memory["memory_id"],
                    "source_event_id": memory["source_event_id"],
                    "reason_codes": ["cross_day", "critical_week_event"],
                    "score": round(memory["importance"] * memory["strength"], 4),
                    "selected": True,
                }
            )

    def _handle_budget_exception(
        self, world_date: str, error: BudgetExceeded
    ) -> None:
        self.degradation_events.append(
            {
                "world_date": world_date,
                "code": error.code,
                "metric": error.metric,
                "handling": "停止本次 mock 生成，保留已提交事件并进入规则模式",
            }
        )

    def _build_report(
        self,
        snapshot_before: dict[str, Any],
        snapshot_after: dict[str, Any],
    ) -> dict[str, Any]:
        events = copy.deepcopy(self.engine.state["events"])
        critical = [
            {
                "template_id": event["template_id"],
                "event_id": event["event_id"],
                "world_date": event["world_date"],
                "visibility": event["visibility"],
            }
            for event in events
            if event["template_id"] in CRITICAL_TEMPLATES
        ]
        public_events = [
            {
                "event_id": event["event_id"],
                "world_date": event["world_date"],
                "occurred_at": event["occurred_at"],
                "template_id": event["template_id"],
                "summary": event["summary"],
            }
            for event in events
            if event["visibility"] == "user_visible"
        ]
        internal_event_ids = {
            event["event_id"]
            for event in events
            if event["visibility"] == "internal"
        }
        observer_memory = [
            {
                "memory_id": memory["memory_id"],
                "kind": memory["kind"],
                "summary": memory["content"],
                "source_event_id": memory["source_event_id"],
            }
            for memory in self.memories
            if memory["state"] == "active"
            and memory["kind"] in {"event", "summary"}
            and memory["source"] != "journal"
            and memory["source_event_id"] not in internal_event_ids
        ][:12]
        observer_projection = {
            "world": {
                "name": snapshot_after["name"],
                "current_date": snapshot_after["world_date"],
                "timezone": snapshot_after["timezone"],
                "locations": [
                    {
                        "location_id": item["location_id"],
                        "name": item["name"],
                        "occupants": item["occupants"],
                    }
                    for item in snapshot_after["locations"].values()
                ],
            },
            "timeline": public_events,
            "daily_shares": copy.deepcopy(self.daily_shares),
            "memory_summary": observer_memory,
            "diary_available": bool(self.diary_records),
            "excluded_private_fields": [
                "internal_journal_content",
                "action_scores",
                "tick_and_prompt",
                "npc_memory_slots",
            ],
        }

        budget_ledger = {
            world_date: budget.to_dict()
            for world_date, budget in self.budgets.items()
        }
        budget_totals = {
            "world_events": sum(item["world_events"] for item in budget_ledger.values()),
            "shares": sum(item["shares"] for item in budget_ledger.values()),
            "journals": sum(item["journals"] for item in budget_ledger.values()),
            "model_calls": sum(item["model_calls"] for item in budget_ledger.values()),
            "review_calls": sum(item["review_calls"] for item in budget_ledger.values()),
            "input_tokens": sum(item["input_tokens"] for item in budget_ledger.values()),
            "output_tokens": sum(item["output_tokens"] for item in budget_ledger.values()),
            "cost_cny": f"{sum(float(item['cost_cny']) for item in budget_ledger.values()):.6f}",
        }

        report = {
            "scenario_id": self.scenario_id,
            "seed": self.seed,
            "start_time": START_TIME,
            "end_time": END_TIME,
            "clock_mode": "frozen",
            "code_version": CODE_VERSION,
            "template_registry_version": TEMPLATE_REGISTRY_VERSION,
            "world_snapshot_before": snapshot_before,
            "ordered_events": events,
            "action_attempts": copy.deepcopy(self.action_attempts),
            "typed_rejections": copy.deepcopy(self.typed_rejections),
            "director_candidates": copy.deepcopy(self.director_candidates),
            "director_rejected_candidates": copy.deepcopy(
                self.director_rejected_candidates
            ),
            "npc_reaction_records": copy.deepcopy(self.npc_reaction_records),
            "memory_read_explanations": copy.deepcopy(self.memory_read_explanations),
            "memory_write_records": copy.deepcopy(self.memory_write_records),
            "relationship_changes": copy.deepcopy(self.relationship_changes),
            "daily_shares": copy.deepcopy(self.daily_shares),
            "diary_records": copy.deepcopy(self.diary_records),
            "observer_visible_projection": observer_projection,
            "budget_ledger": {
                "daily": budget_ledger,
                "totals": budget_totals,
            },
            "degradation_events": copy.deepcopy(self.degradation_events),
            "fault_cases": copy.deepcopy(self.fault_cases),
            "world_snapshot_after": snapshot_after,
            "replay_hashes": {
                "snapshot_before": digest(snapshot_before),
                "snapshot_after": digest(snapshot_after),
                "business_result": digest(
                    {
                        "events": events,
                        "actions": self.action_attempts,
                        "relationships": snapshot_after["relationships"],
                        "memories": self.memories,
                        "npc_reactions": self.npc_reaction_records,
                        "budget": budget_ledger,
                        "shares": self.daily_shares,
                    }
                ),
            },
            "critical_events": critical,
            "known_limitations": [
                "B1 使用内存快照，不包含 B4 的 SQLite/PostgreSQL 持久化。",
                "B1 仅实现 rule_only；真实 LLM、审核供应商和计费均未接入。",
                "B1 以固定路线验证世界边界，完整 Intent 候选规划由 B2 扩展。",
                "B1 为满足冻结的日终路线，移动会沿公开地点图自动选择最短可达路径；B2 将收敛为单跳动作候选。",
                "河边活动自带午餐与日终日记位置按冻结场景夹具处理，后续批次需补充资源库存。",
            ],
            "scenario_summary": {
                "dates": list(DAILY_ROUTES),
                "location_count": len(snapshot_after["locations"]),
                "npc_count": len(snapshot_after["npcs"]),
                "action_count": len(ACTIONS),
                "director_template_count": len(DIRECTOR_TEMPLATES),
                "critical_expected": len(
                    {
                        template
                        for templates in SHARE_EXPECTED_TEMPLATES.values()
                        for template in templates
                    }
                ),
                "critical_seen": len({item["template_id"] for item in critical}),
            },
        }
        return report


def terminal_summary(report: dict[str, Any]) -> str:
    summary = report["scenario_summary"]
    totals = report["budget_ledger"]["totals"]
    rejection_count = len(report["typed_rejections"])
    critical_ok = summary["critical_seen"] == summary["critical_expected"]
    return "\n".join(
        [
            "B1 七日规则模拟完成",
            f"场景：{report['scenario_id']}",
            f"seed：{report['seed']}",
            f"日期：{summary['dates'][0]} 至 {summary['dates'][-1]}",
            f"关键事件：{summary['critical_seen']}/{summary['critical_expected']} "
            f"（{'通过' if critical_ok else '未通过'}）",
            f"实体：{summary['npc_count']} 名 NPC，{summary['location_count']} 个地点，"
            f"{summary['action_count']} 个动作，{summary['director_template_count']} 个导演模板",
            f"事件：{totals['world_events']} 个世界事件，{totals['shares']} 次分享，"
            f"{totals['journals']} 篇私密日记",
            f"mock 预算：{totals['model_calls']} 次生成，"
            f"{totals['input_tokens']}/{totals['output_tokens']} tokens，"
            f"估算 {totals['cost_cny']} 元",
            f"拒绝：{rejection_count} 个类型化动作失败",
            f"业务快照：{report['replay_hashes']['business_result']}",
        ]
    )
