"""Live DeepSeek deployment smoke command."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from rpg_orm.migrations import create_database_engine

from .runtime import LlmRuntimeConfig, build_gateway, daily_share_request


CHINA_TIMEZONE = timezone(timedelta(hours=8))


def main() -> int:
    parser = argparse.ArgumentParser(description="DeepSeek live smoke")
    parser.add_argument("--url", required=True)
    parser.add_argument("--budget-date")
    parser.add_argument("--operation-id")
    parser.add_argument("--output")
    parser.add_argument("--allow-fallback", action="store_true")
    args = parser.parse_args()
    now = datetime.now(CHINA_TIMEZONE)
    budget_date = args.budget_date or now.date().isoformat()
    operation_id = args.operation_id or (
        "deepseek-smoke-" + now.strftime("%Y%m%dT%H%M%SZ")
    )
    engine = create_database_engine(args.url)
    try:
        gateway, config = build_gateway(engine, LlmRuntimeConfig.from_env())
        request = daily_share_request(
            operation_id=operation_id,
            world_date=budget_date,
            summaries=[
                "清晨的操场完成了例行检查。",
                "食堂公布了当天的公开菜单。",
                "图书馆延长了晚间开放时间。",
            ],
            budget_date=budget_date,
        )
        result = gateway.generate(request)
    finally:
        engine.dispose()
    payload = {
        "schema_version": "rpg-llm-smoke-v1",
        "checked_at": now.isoformat().replace("+00:00", "Z"),
        "operation_id": operation_id,
        "runtime": config.safe_summary(),
        "result": result,
        "live": (
            result.get("status") == "succeeded"
            and result.get("provider") == "deepseek"
        ),
    }
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    print(json.dumps(payload, ensure_ascii=False, default=str))
    if args.allow_fallback:
        return 0
    return 0 if payload["live"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
