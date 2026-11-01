"""Reproducible seven-day integration quality report."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rpg_sim.ids import digest
from rpg_sim.simulator import SevenDaySimulator

from .detectors import run_release_gates


def run_seven_day_e2e(root: Path) -> dict[str, Any]:
    simulation = SevenDaySimulator().run()
    if not simulation.complete:
        raise RuntimeError("七日端到端模拟未完成")
    report = simulation.report
    quality = run_release_gates(report, root=root)
    finding_counts = {}
    for finding in quality.findings:
        finding_counts[finding.code] = (
            finding_counts.get(finding.code, 0) + 1
        )
    summary = {
        "schema_version": "rpg-b10-e2e-v1",
        "status": "passed" if quality.passed else "blocked",
        "seed": report["seed"],
        "scenario_id": report["scenario_id"],
        "days": len(report["budget_ledger"]["daily"]),
        "event_count": len(report["ordered_events"]),
        "npc_reaction_count": len(report["npc_reaction_records"]),
        "business_hash": report["replay_hashes"]["business_result"],
        "simulation_hash": digest(
            {
                "business": report["replay_hashes"],
                "quality": quality.to_dict(),
            }
        ),
        "quality": quality.to_dict(),
        "finding_counts": finding_counts,
    }
    return summary
