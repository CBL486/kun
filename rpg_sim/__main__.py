"""B1 命令行入口。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .ids import canonical_json
from .scenario import SCENARIO_ID, SEED
from .simulator import SevenDaySimulator, SimulationError, terminal_summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m rpg_sim",
        description="运行青禾镇确定性七日规则模拟",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    seven_day = subparsers.add_parser("seven-day", help="运行七天切片")
    seven_day.add_argument("--scenario", default=SCENARIO_ID)
    seven_day.add_argument("--seed", type=int, default=SEED)
    seven_day.add_argument("--mode", default="rule_only", choices=["rule_only"])
    seven_day.add_argument("--frozen-clock", action="store_true")
    seven_day.add_argument("--output", type=Path, required=True)
    seven_day.add_argument(
        "--pause-after",
        type=int,
        default=None,
        help="本次运行完成指定动作步数后保存检查点并暂停",
    )
    seven_day.add_argument(
        "--resume",
        action="store_true",
        help="从输出目录中的 checkpoint.json 继续",
    )
    seven_day.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="终端摘要格式；完整结构化报告始终写入 output 目录",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command != "seven-day":
        return 2
    if not args.frozen_clock:
        print("B1 必须提供 --frozen-clock", file=sys.stderr)
        return 2
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    checkpoint = output / "checkpoint.json"
    try:
        result = SevenDaySimulator(
            scenario_id=args.scenario,
            seed=args.seed,
            mode=args.mode,
            frozen_clock=args.frozen_clock,
            checkpoint_path=checkpoint,
            resume=args.resume,
            pause_after_steps=args.pause_after,
        ).run()
    except SimulationError as error:
        print(f"模拟失败：{error}", file=sys.stderr)
        return 2

    (output / "run.json").write_text(
        json.dumps(result.report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "snapshot-before.json").write_text(
        json.dumps(result.snapshot_before, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "snapshot-after.json").write_text(
        json.dumps(result.snapshot_after, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if not result.complete:
        progress = result.report["progress"]
        pause_summary = "\n".join(
            [
                "B1 七日规则模拟已暂停",
                f"已完成日期索引：{progress['day_index']}",
                f"当前阶段：{progress['phase']}",
                f"检查点：{checkpoint}",
                "继续命令：",
                f"python -m rpg_sim seven-day --output {output} "
                "--mode rule_only --frozen-clock --resume",
            ]
        )
        (output / "summary.md").write_text(
            "# B1 七日模拟暂停\n\n```text\n" + pause_summary + "\n```\n",
            encoding="utf-8",
        )
        if args.format == "json":
            print(canonical_json(result.report))
        else:
            print(pause_summary)
        return 0

    (output / "replay-manifest.json").write_text(
        json.dumps(result.report["replay_hashes"], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (output / "summary.md").write_text(
        "# B1 七日模拟摘要\n\n```text\n"
        + terminal_summary(result.report)
        + "\n```\n",
        encoding="utf-8",
    )

    if args.format == "json":
        print(canonical_json(result.report))
    else:
        print(terminal_summary(result.report))
        print(f"输出目录：{output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
