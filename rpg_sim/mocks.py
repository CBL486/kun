"""B1 离线 LLM 与内容审核 mock。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .ids import digest


@dataclass(frozen=True)
class MockLLMResponse:
    text: Any
    input_tokens: int
    output_tokens: int
    provider: str = "mock"


class MockLLM:
    """不联网的确定性生成器，只生成预先定义的规则文本。"""

    def __init__(self, seed: int):
        self.seed = seed

    def complete(self, operation: str, payload: dict[str, Any]) -> MockLLMResponse:
        if operation == "daily_share":
            summaries = payload["summaries"]
            text = {
                "event": "今天发生了：" + "；".join(summaries),
                "feeling": "这些安排让林澄既有一点紧张，也觉得事情在逐步变清楚。",
                "reflection": "林澄想把已经确认的事实和尚未说清的分歧分开记下，再决定下一步。",
            }
            return MockLLMResponse(
                text=text,
                input_tokens=760,
                output_tokens=240,
            )
        if operation == "observer_message_ack":
            return MockLLMResponse(
                text="留言已收下，会在下一个合法时段按角色自己的意愿处理。",
                input_tokens=100,
                output_tokens=30,
            )
        fingerprint = digest({"seed": self.seed, "operation": operation})[:12]
        return MockLLMResponse(
            text=f"mock-{operation}-{fingerprint}",
            input_tokens=80,
            output_tokens=20,
        )


class MockReviewer:
    """B1 使用的确定性审核器。"""

    policy_version = "mvp-content-v1"

    def review(self, content: Any) -> str:
        if not content:
            return "blocked"
        return "approved"
