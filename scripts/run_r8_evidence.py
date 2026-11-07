"""Generate deterministic R8 evidence using fixtures only."""

from __future__ import annotations

import json
import tempfile
from datetime import datetime
from pathlib import Path

from app.media_observer import (
    MediaObservationService,
    MediaSummary,
    PublicMetadata,
    StaticMediaSummarizer,
)
from rpg_llm.models import ReviewDecision
from rpg_orm.migrations import create_database_engine
from rpg_orm.product_repository import ProductRepository


class FixtureFetcher:
    def fetch(self, provider, url):
        return PublicMetadata(
            provider=provider,
            canonical_url=url,
            title="公开视频：记忆与告别",
            description="一段讨论记忆、倾听与告别的公开简介。",
        )

    def fetch_bilibili_hot(self, *, limit=10):
        return [
            PublicMetadata(
                provider="bilibili",
                canonical_url="https://www.bilibili.com/video/BVhotR8",
                title="公开热门视频",
                description="公开简介",
            )
        ]


class FixtureReviewer:
    policy_version = "fixture-v1"

    def review(self, content, structured):
        return ReviewDecision(
            status="approved",
            provider="fixture-review",
            policy_version=self.policy_version,
        )


def main() -> None:
    root = Path(tempfile.mkdtemp(prefix="aiworld-r8-evidence-"))
    engine = create_database_engine(
        f"sqlite:///{(root / 'media.db').as_posix()}"
    )
    try:
        repository = ProductRepository(engine)
        service = MediaObservationService(
            repository,
            fetcher=FixtureFetcher(),
            summarizer=StaticMediaSummarizer(),
            reviewer=FixtureReviewer(),
        )
        first = service.observe(
            provider="bilibili",
            url="https://www.bilibili.com/video/BVfixtureR8",
            now=datetime.fromisoformat("2026-11-07T15:00:00+08:00"),
        )
        replay = service.observe(
            provider="bilibili",
            url="https://www.bilibili.com/video/BVfixtureR8",
            now=datetime.fromisoformat("2026-11-07T15:01:00+08:00"),
        )
        hot = service.observe_bilibili_hot(
            limit=3,
            now=datetime.fromisoformat("2026-11-07T15:02:00+08:00"),
        )
        event = repository.get_memory_event(first["memory_event_id"])
        payload = {
            "schema_version": "aiworld-r8-evidence-v1",
            "network_mode": "fixture",
            "first": first,
            "replay": replay,
            "hot": hot,
            "event": {
                "visibility": event["visibility"],
                "source": event["source"],
                "importance": event["importance"],
            },
        }
        output = (
            Path(__file__).resolve().parents[1]
            / "docs"
            / "r8-evidence-2026-11-07.json"
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
