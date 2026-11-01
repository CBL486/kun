"""Local B9 operation and cost audit."""

from __future__ import annotations

import argparse
import json

from rpg_orm.migrations import create_database_engine

from .repository import LlmRepository


def main() -> int:
    parser = argparse.ArgumentParser(description="B9 LLM 成本与操作审计")
    parser.add_argument("--url", required=True)
    parser.add_argument("--budget-date", required=True)
    args = parser.parse_args()

    engine = create_database_engine(args.url)
    try:
        repository = LlmRepository(engine)
        budget = repository.usage_snapshot(args.budget_date)
        payload = {
            "budget_date": args.budget_date,
            "usage": {
                "calls": budget.calls,
                "review_calls": budget.review_calls,
                "input_tokens": budget.input_tokens,
                "output_tokens": budget.output_tokens,
                "cost_cny": str(budget.cost_cny),
            },
            "records": repository.list_usage(),
        }
    finally:
        engine.dispose()
    print(json.dumps(payload, ensure_ascii=False, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
