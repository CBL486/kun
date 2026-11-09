"""Capture Gate A R2 matrices in the real game page."""

from __future__ import annotations

import json
from pathlib import Path

import capture_character_gate_a_r1_maps as capture


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    capture.OUTPUT_ROOT = (
        ROOT / "art-source" / "character-v2" / "gate-a-r2"
    )
    capture.REPORT_PATH = (
        ROOT
        / "docs"
        / "character-art-v2"
        / "gate-a-r2-map-evidence.json"
    )
    result = capture.main()
    if result != 0:
        return result
    report = json.loads(
        capture.REPORT_PATH.read_text(encoding="utf-8")
    )
    report["schema_version"] = (
        "rpg-character-gate-a-r2-map-evidence-v1"
    )
    report["source_root"] = (
        "art-source/character-v2/gate-a-r2"
    )
    capture.REPORT_PATH.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
