"""Read one public Bilibili OG record without credentials or writeback."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from app.media_observer import (
    HttpPublicMediaFetcher,
    MediaObservationService,
    StaticMediaSummarizer,
)
from rpg_orm.migrations import create_database_engine
from rpg_orm.product_repository import ProductRepository


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url",
        default="https://www.bilibili.com/video/BV1GJ411x7h7",
    )
    args = parser.parse_args()
    root = Path(tempfile.mkdtemp(prefix="aiworld-r9-public-media-"))
    engine = create_database_engine(
        f"sqlite:///{(root / 'media.db').as_posix()}"
    )
    try:
        repository = ProductRepository(engine)
        service = MediaObservationService(
            repository,
            fetcher=HttpPublicMediaFetcher(),
            summarizer=StaticMediaSummarizer(),
            daily_limit=1,
            token_budget=600,
        )
        observation = service.observe(
            provider="bilibili",
            url=args.url,
        )
        event = repository.get_memory_event(observation["memory_event_id"])
        payload = {
            "schema_version": "aiworld-r9-public-media-smoke-v1",
            "network_mode": "public_og_read_only",
            "credentials_sent": False,
            "automatic_interactions": False,
            "observation": observation,
            "memory_event": {
                "visibility": event["visibility"],
                "source": event["source"],
                "importance": event["importance"],
            },
        }
        output = (
            Path(__file__).resolve().parents[1]
            / "docs"
            / "r9-public-media-smoke-2026-11-08.json"
        )
        output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(output)
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
