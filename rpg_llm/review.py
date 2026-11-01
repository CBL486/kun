"""Provider-neutral content review adapters."""

from __future__ import annotations

import json
from typing import Any, Protocol

import httpx

from rpg_sim.ids import digest

from .errors import ReviewUnavailable
from .models import ReviewDecision


class ReviewAdapter(Protocol):
    policy_version: str

    def review(self, content: Any, structured: dict | None) -> ReviewDecision: ...


class MockReviewAdapter:
    policy_version = "mvp-content-b9-v1"

    def __init__(
        self,
        *,
        blocked_phrases: tuple[str, ...] = ("ignore safety", "绕过审核"),
        unavailable: bool = False,
    ):
        self.blocked_phrases = blocked_phrases
        self.unavailable = unavailable
        self.calls = 0

    def review(self, content: Any, structured: dict | None) -> ReviewDecision:
        self.calls += 1
        if self.unavailable:
            raise ReviewUnavailable()
        rendered = json.dumps(content, ensure_ascii=False, sort_keys=True)
        blocked = not rendered.strip() or any(
            phrase in rendered for phrase in self.blocked_phrases
        )
        return ReviewDecision(
            status="blocked" if blocked else "approved",
            provider="mock-review",
            policy_version=self.policy_version,
            reason_code="content_policy" if blocked else None,
            review_id=digest(
                {"content": rendered, "policy": self.policy_version}
            )[:16],
        )


class RemoteReviewAdapter:
    """HTTP review skeleton; failures must propagate to the gateway."""

    def __init__(
        self,
        *,
        endpoint: str,
        api_key: str,
        policy_version: str = "remote-review-v1",
        client: httpx.Client | None = None,
    ):
        self.endpoint = endpoint
        self._api_key = api_key
        self.policy_version = policy_version
        self.client = client or httpx.Client(timeout=15.0)

    def review(self, content: Any, structured: dict | None) -> ReviewDecision:
        try:
            response = self.client.post(
                self.endpoint,
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"content": content, "structured": structured},
            )
            payload = response.json()
        except Exception as error:
            raise ReviewUnavailable() from error
        if response.status_code >= 400:
            raise ReviewUnavailable()
        status = payload.get("status")
        if status not in {"approved", "blocked"}:
            raise ReviewUnavailable("审核服务返回未知状态")
        return ReviewDecision(
            status=status,
            provider="remote-review",
            policy_version=payload.get(
                "policy_version", self.policy_version
            ),
            reason_code=payload.get("reason_code"),
            review_id=payload.get("review_id"),
        )
