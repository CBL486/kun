"""主智能体状态机与 B1 世界引擎适配。"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any

from rpg_sim.engine import WorldEngine
from rpg_sim.ids import digest, stable_id
from rpg_sim.scenario import MAIN_ID, WORLD_ID

from .models import (
    ActionIntent,
    DecisionTrace,
    IntentProposal,
    IntentValidationError,
)
from .perception import Perception
from .planner import RulePlanner


@dataclass
class AgentStepResult:
    status: str
    perception: Perception
    trace: DecisionTrace
    proposal: IntentProposal
    intent: ActionIntent
    world_result: dict[str, Any]
    recovery_attempts: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "perception": self.perception.to_dict(),
            "decision_trace": self.trace.to_dict(),
            "proposal": self.proposal.to_dict(),
            "action_intent": self.intent.to_dict(),
            "world_result": self.world_result,
            "recovery_attempts": self.recovery_attempts,
        }


class AgentLoop:
    def __init__(
        self,
        engine: WorldEngine,
        *,
        seed: int = 20261028,
        planner: RulePlanner | None = None,
    ):
        self.engine = engine
        self.seed = seed
        self.planner = planner or RulePlanner(seed)
        self.intent_cache: dict[
            str,
            tuple[Perception, DecisionTrace, IntentProposal, ActionIntent],
        ] = {}

    def prepare(self, world_date: str, time_text: str, slot_key: str) -> None:
        self.engine.prepare_time(world_date, time_text, slot_key)

    def perceive(self) -> Perception:
        return Perception.from_world(self.engine.state, self._tick_id())

    def plan(
        self,
        perception: Perception | None = None,
        *,
        degradation_reason: str | None = None,
    ) -> DecisionTrace:
        perception = perception or self.perceive()
        return self.planner.plan(
            self.engine.state,
            perception,
            degradation_reason=degradation_reason,
        )

    def propose(
        self,
        operation_id: str,
        trace: DecisionTrace | None = None,
    ) -> IntentProposal:
        trace = trace or self.plan()
        if not trace.selected_candidate_id:
            raise IntentValidationError("no_op", "没有可提出的合法动作")
        selected = next(
            candidate
            for candidate in trace.candidates
            if candidate.candidate_id == trace.selected_candidate_id
        )
        proposal = IntentProposal.from_candidate(
            candidate=selected,
            operation_id=operation_id,
            tick_id=trace.tick_id,
            character_id=MAIN_ID,
        )
        proposal.validate()
        return proposal

    def materialize(
        self,
        proposal: IntentProposal,
        *,
        expected_state_version: int | None = None,
        source_candidate_id: str | None = None,
    ) -> ActionIntent:
        nonce = digest(
            {
                "operation_id": proposal.operation_id,
                "intent_id": proposal.intent_id,
            }
        )[:16]
        action_id = stable_id(
            "act",
            [proposal.tick_id, 0, nonce],
        )
        return ActionIntent(
            schema_version="rpg-action-intent-v1",
            action_id=action_id,
            operation_id=proposal.operation_id,
            tick_id=proposal.tick_id,
            world_id=WORLD_ID,
            character_id=MAIN_ID,
            action_type=proposal.action_type,
            target_id=proposal.target_id,
            parameters=dict(proposal.parameters),
            expected_state_version=(
                self.engine.state["state_version"]
                if expected_state_version is None
                else expected_state_version
            ),
            origin="rule_engine",
            intent_nonce=nonce,
            source_candidate_id=source_candidate_id,
        )

    def run_once(
        self,
        operation_id: str,
        *,
        simulate_model_error: bool = False,
        reuse_cached_intent: bool = True,
    ) -> AgentStepResult:
        cached_step = self.intent_cache.get(operation_id)
        if reuse_cached_intent and cached_step:
            perception, trace, proposal, intent = cached_step
            world_result = self.engine.apply(
                intent.to_world_payload(),
                event_template_id=None,
            )
            return AgentStepResult(
                status=self._status(world_result, trace.degradation_reason),
                perception=perception,
                trace=trace,
                proposal=proposal,
                intent=intent,
                world_result=world_result,
            )
        perception = self.perceive()
        degradation = (
            "model_format_error: 规则模式接管"
            if simulate_model_error
            else None
        )
        trace = self.plan(perception, degradation_reason=degradation)
        proposal = self.propose(operation_id, trace)
        intent = self.materialize(
            proposal,
            source_candidate_id=trace.selected_candidate_id,
        )
        if reuse_cached_intent:
            self.intent_cache[operation_id] = (
                perception,
                trace,
                proposal,
                intent,
            )
        world_result = self.engine.apply(
            intent.to_world_payload(),
            event_template_id=None,
        )
        status = self._status(world_result, degradation)
        return AgentStepResult(
            status=status,
            perception=perception,
            trace=trace,
            proposal=proposal,
            intent=intent,
            world_result=world_result,
        )

    def execute(self, intent: ActionIntent) -> dict[str, Any]:
        return self.engine.apply(intent.to_world_payload())

    def recover_after_stale(self, operation_id: str) -> AgentStepResult:
        """状态过期后重新读取快照并重新规划同一逻辑 operation。"""
        self.intent_cache.pop(operation_id, None)
        return self.run_once(operation_id, reuse_cached_intent=False)

    def _tick_id(self) -> str:
        state = self.engine.state
        return stable_id(
            "tick",
            [
                state["world_id"],
                MAIN_ID,
                state["world_date"],
                state["open_slot"],
                f"{state['world_date']}:{state['open_slot']}",
            ],
        )

    @staticmethod
    def _status(world_result: dict[str, Any], degradation: str | None) -> str:
        if not world_result["ok"]:
            return "REJECTED"
        if world_result["replayed"]:
            return "COMMITTED"
        if degradation:
            return "DEGRADED"
        return "COMMITTED"
