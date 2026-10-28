"""B3 NPC 日程演示入口。"""

from __future__ import annotations

import argparse
import json

from .runtime import NPCRuntime


def main() -> int:
    parser = argparse.ArgumentParser(description="输出四名 NPC 的确定性日程")
    parser.add_argument("--date", default="2026-11-04")
    args = parser.parse_args()
    runtime = NPCRuntime()
    print(
        json.dumps(
            runtime.run_day(args.date),
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
