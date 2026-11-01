"""Run B10 seven-day quality verification locally."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .e2e import run_seven_day_e2e


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser(description="B10 七日质量门禁")
    parser.add_argument(
        "--output",
        default=str(ROOT / "out" / "b10" / "e2e-report.json"),
    )
    args = parser.parse_args()
    output = Path(args.output).resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    report = run_seven_day_e2e(ROOT)
    output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(output)
    print(
        json.dumps(
            {
                "status": report["status"],
                "events": report["event_count"],
                "errors": report["quality"]["error_count"],
                "warnings": report["quality"]["warning_count"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
