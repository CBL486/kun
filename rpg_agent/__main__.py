"""B2 主智能体核心的本地演示入口。"""

from __future__ import annotations

import argparse
import json

from rpg_sim.engine import WorldEngine
from rpg_sim.scenario import initial_world

from .loop import AgentLoop


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 B2 主智能体单步演示")
    parser.add_argument("--date", default="2026-11-02")
    parser.add_argument("--time", default="06:50")
    parser.add_argument("--slot", default="dawn")
    parser.add_argument("--operation-id", default="op_b2_demo_001")
    args = parser.parse_args()

    loop = AgentLoop(WorldEngine(initial_world()))
    loop.prepare(args.date, args.time, args.slot)
    result = loop.run_once(args.operation_id)
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
    return 0 if result.world_result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
