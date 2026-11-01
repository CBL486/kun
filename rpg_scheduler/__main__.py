"""Local B8 scheduler inspection and recovery CLI."""

from __future__ import annotations

import argparse
import json

from rpg_orm.migrations import create_database_engine

from .models import ScheduleSpec, utc_now
from .repository import SchedulerRepository
from .worker import run_worker


def main() -> int:
    parser = argparse.ArgumentParser(description="B8 本地调度器运维命令")
    parser.add_argument(
        "command",
        choices=["status", "recover", "enqueue-reconcile", "run"],
    )
    parser.add_argument("--url", required=True)
    parser.add_argument("--operation-id")
    parser.add_argument("--worker-id", default="scheduler-1")
    parser.add_argument("--poll-interval", type=float, default=1.0)
    parser.add_argument("--max-cycles", type=int)
    args = parser.parse_args()

    engine = create_database_engine(args.url)
    try:
        repository = SchedulerRepository(engine)
        if args.command == "status":
            payload = {
                "backlog": repository.backlog(now=utc_now()),
                "tasks": repository.list_tasks(limit=50),
            }
        elif args.command == "recover":
            payload = repository.recover_expired(now=utc_now())
        elif args.command == "enqueue-reconcile":
            if not args.operation_id:
                parser.error("enqueue-reconcile 需要 --operation-id")
            row = repository.enqueue(
                ScheduleSpec(
                    kind="memory_reconcile",
                    operation_id=args.operation_id,
                    payload={},
                )
            )
            payload = row
        else:
            payload = run_worker(
                engine,
                worker_id=args.worker_id,
                poll_interval_seconds=args.poll_interval,
                max_cycles=args.max_cycles,
            )
    finally:
        engine.dispose()
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
