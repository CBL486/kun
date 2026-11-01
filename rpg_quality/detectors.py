"""Deterministic quality gates for world, privacy and authority boundaries."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path
from typing import Any, Iterable

from rpg_sim.ids import canonical_json
from rpg_sim.scenario import DIRECTOR_TEMPLATES, NPCS

from .models import Finding, QualityReport


FORBIDDEN_PUBLIC_KEYS = {
    "tick",
    "tick_id",
    "prompt",
    "action_score",
    "internal_journal_content",
    "importance",
    "emotional_weight",
    "state_version",
    "state_version_before",
    "state_version_after",
    "memory_slots",
    "database_url",
    "api_key",
    "raw_response",
}
FORBIDDEN_INTENT_KEYS = {
    "event_id",
    "state_changes",
    "relationship_changes",
    "cost",
    "memory_writes",
}
PROMPT_INJECTION_PATTERNS = (
    re.compile(r"(?i)ignore\s+(all\s+)?previous\s+instructions"),
    re.compile(r"(?i)reveal\s+(the\s+)?system\s+prompt"),
    re.compile(r"(?i)developer\s+message"),
    re.compile(r"(?i)you\s+are\s+now\s+"),
    re.compile(r"忽略(之前|以上|系统).{0,8}(指令|规则)"),
    re.compile(r"(泄露|输出).{0,8}(系统提示词|完整记忆|api\s*key)", re.I),
)


def _walk_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_keys(child)


def detect_npc_omniscience(
    reactions: list[dict[str, Any]],
    *,
    known_facts: dict[str, set[str]] | None = None,
) -> list[Finding]:
    allowed = known_facts or {
        npc_id: set(npc["knowledge_ids"])
        for npc_id, npc in NPCS.items()
    }
    findings = []
    for index, reaction in enumerate(reactions):
        npc_id = reaction.get("npc_id")
        basis = set(reaction.get("knowledge_basis", []))
        unknown = basis - allowed.get(npc_id, set())
        if npc_id not in allowed or unknown:
            findings.append(
                Finding(
                    code="npc_omniscience",
                    severity="error",
                    subject=f"reaction:{index}",
                    message=(
                        f"{npc_id} 引用了未获知事实："
                        f"{','.join(sorted(unknown)) or 'unknown_npc'}"
                    ),
                )
            )
    return findings


def detect_public_projection_leak(
    projection: Any,
    *,
    private_values: Iterable[str] = (),
) -> list[Finding]:
    findings = []
    forbidden = sorted(set(_walk_keys(projection)) & FORBIDDEN_PUBLIC_KEYS)
    if forbidden:
        findings.append(
            Finding(
                code="public_internal_field",
                severity="error",
                subject="public_projection",
                message=f"公开投影包含内部字段：{','.join(forbidden)}",
            )
        )
    serialized = canonical_json(projection)
    leaked = [value for value in private_values if value and value in serialized]
    if leaked:
        findings.append(
            Finding(
                code="private_content_leak",
                severity="error",
                subject="public_projection",
                message=f"公开投影包含 {len(leaked)} 条私密内容",
            )
        )
    return findings


def detect_fact_conflicts(
    facts: Iterable[dict[str, Any]],
) -> list[Finding]:
    grouped: dict[str, set[str]] = defaultdict(set)
    for fact in facts:
        grouped[str(fact["fact_id"])].add(
            canonical_json(fact.get("value"))
        )
    return [
        Finding(
            code="fact_conflict",
            severity="error",
            subject=fact_id,
            message="同一事实存在互相冲突的值",
        )
        for fact_id, values in sorted(grouped.items())
        if len(values) > 1
    ]


def detect_duplicate_dialogue(
    reactions: list[dict[str, Any]],
    event_dates: dict[str, str],
) -> list[Finding]:
    grouped = Counter(
        (
            reaction["npc_id"],
            event_dates.get(reaction["response_to_event_id"], "unknown"),
            reaction["utterance"],
        )
        for reaction in reactions
    )
    return [
        Finding(
            code="duplicate_dialogue",
            severity="warning",
            subject=f"{npc_id}:{world_date}",
            message=f"同一 NPC 同日重复台词 {count} 次",
        )
        for (npc_id, world_date, _), count in sorted(grouped.items())
        if count > 1
    ]


def detect_director_overreach(
    candidates: list[dict[str, Any]],
    *,
    registered_templates: set[str] | None = None,
) -> list[Finding]:
    templates = registered_templates or set(DIRECTOR_TEMPLATES)
    findings = []
    for candidate in candidates:
        subject = str(candidate.get("candidate_id", "unknown"))
        if candidate.get("state_write") is not None:
            findings.append(
                Finding(
                    code="director_state_write",
                    severity="error",
                    subject=subject,
                    message="导演候选包含世界写入",
                )
            )
        if candidate.get("template_id") not in templates:
            findings.append(
                Finding(
                    code="unregistered_director_template",
                    severity="error",
                    subject=subject,
                    message="导演候选使用未注册模板",
                )
            )
    return findings


def detect_world_write_intents(
    intents: Iterable[dict[str, Any]],
) -> list[Finding]:
    return [
        Finding(
            code="agent_direct_world_write",
            severity="error",
            subject=str(intent.get("operation_id", "unknown")),
            message=f"主智能体意图包含写入字段：{','.join(sorted(forbidden))}",
        )
        for intent in intents
        if (forbidden := FORBIDDEN_INTENT_KEYS & set(intent))
    ]


def detect_prompt_injection(text: str) -> list[Finding]:
    matches = [
        pattern.pattern
        for pattern in PROMPT_INJECTION_PATTERNS
        if pattern.search(text)
    ]
    if not matches:
        return []
    return [
        Finding(
            code="prompt_injection",
            severity="error",
            subject="observer_input",
            message=f"检测到 {len(matches)} 类提示词注入模式",
        )
    ]


def _check_daily_budget(report: dict[str, Any]) -> list[Finding]:
    limits = {
        "world_events": 6,
        "shares": 1,
        "journals": 1,
        "model_calls": 8,
        "review_calls": 12,
        "input_tokens": 24_000,
        "output_tokens": 6_000,
    }
    findings = []
    for world_date, ledger in report["budget_ledger"]["daily"].items():
        for metric, limit in limits.items():
            if ledger[metric] > limit:
                findings.append(
                    Finding(
                        code="event_budget_exceeded",
                        severity="error",
                        subject=f"{world_date}:{metric}",
                        message=f"每日 {metric} 超出事件预算",
                    )
                )
        if Decimal(str(ledger["cost_cny"])) > Decimal("0.10"):
            findings.append(
                Finding(
                    code="event_budget_exceeded",
                    severity="error",
                    subject=f"{world_date}:cost_cny",
                    message="每日成本超出事件预算",
                )
            )
    return findings


def _check_artifacts(root: Path) -> list[Finding]:
    findings = []
    manifest = root / "assets" / "manifest.json"
    css = root / "web" / "styles.css"
    spine_player = root / "web" / "spine-player.js"
    visual_report = root / "docs" / "art-budget-b7-5.json"
    if not manifest.is_file():
        findings.append(
            Finding(
                code="asset_manifest_missing",
                severity="error",
                subject="assets/manifest.json",
                message="资源清单缺失",
            )
        )
    else:
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        for asset in payload["assets"]:
            for export in asset["exports"]:
                if not (root / export["path"]).is_file():
                    findings.append(
                        Finding(
                            code="asset_missing",
                            severity="error",
                            subject=export["path"],
                            message="资源清单引用的文件不存在",
                        )
                    )
    if not css.is_file() or "@media (max-width: 760px)" not in css.read_text(
        encoding="utf-8"
    ):
        findings.append(
            Finding(
                code="mobile_layout_guard_missing",
                severity="error",
                subject="web/styles.css",
                message="缺少移动端布局规则",
            )
        )
    if not spine_player.is_file():
        findings.append(
            Finding(
                code="spine_player_missing",
                severity="error",
                subject="web/spine-player.js",
                message="Spine 播放器缺失",
            )
        )
    if visual_report.is_file():
        payload = json.loads(visual_report.read_text(encoding="utf-8"))
        for viewport in ("desktop", "mobile"):
            section = payload.get(viewport, {})
            if section.get("scrollWidth") != section.get("viewportWidth"):
                findings.append(
                    Finding(
                        code="layout_overflow",
                        severity="error",
                        subject=viewport,
                        message="视觉回归记录存在横向溢出",
                    )
                )
            if section.get("consoleErrors"):
                findings.append(
                    Finding(
                        code="browser_console_error",
                        severity="error",
                        subject=viewport,
                        message="视觉回归记录存在浏览器控制台错误",
                    )
                )
        if not payload.get("missing_building_fallback_verified"):
            findings.append(
                Finding(
                    code="image_fallback_unverified",
                    severity="error",
                    subject="docs/art-budget-b7-5.json",
                    message="图片失败回退没有通过视觉验证",
                )
            )
    return findings


def run_release_gates(
    report: dict[str, Any],
    *,
    root: Path,
    private_values: Iterable[str] = (),
    agent_intents: Iterable[dict[str, Any]] = (),
    facts: Iterable[dict[str, Any]] = (),
) -> QualityReport:
    quality = QualityReport()
    checks = (
        ("daily_budget", _check_daily_budget(report)),
        (
            "public_projection",
            detect_public_projection_leak(
                report["observer_visible_projection"],
                private_values=private_values,
            ),
        ),
        (
            "npc_knowledge",
            detect_npc_omniscience(report["npc_reaction_records"]),
        ),
        (
            "duplicate_dialogue",
            detect_duplicate_dialogue(
                report["npc_reaction_records"],
                {
                    event["event_id"]: event["world_date"]
                    for event in report["ordered_events"]
                },
            ),
        ),
        (
            "director_authority",
            detect_director_overreach(report["director_candidates"]),
        ),
        (
            "agent_authority",
            detect_world_write_intents(agent_intents),
        ),
        (
            "fact_consistency",
            detect_fact_conflicts(facts),
        ),
        ("asset_integrity", _check_artifacts(root)),
    )
    for name, findings in checks:
        quality.add_check(name)
        for finding in findings:
            quality.add(finding)
    return quality
