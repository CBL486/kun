"""Deterministic safe templates used when model output is unavailable."""

from __future__ import annotations

from typing import Any

from .models import LlmRequest


def rule_fallback(request: LlmRequest) -> tuple[Any, dict[str, Any] | None]:
    if request.template_id == "daily_share":
        summaries = request.variables.get("summaries", [])
        visible = "；".join(str(item) for item in summaries[:5])
        return (
            {
                "event": f"今天发生了：{visible}" if visible else "今天没有新增公开事件。",
                "feeling": "林澄先保持平静，等确认事实后再表达感受。",
                "reflection": "先整理已经公开的事实，未确认的内容留到之后。",
            },
            None,
        )
    if request.template_id == "action_candidate":
        return (
            "按当前公开状态保持原计划。",
            {
                "action_type": "rest",
                "target_id": None,
                "parameters": {},
                "confidence": 0.5,
            },
        )
    if request.template_id == "media_observation":
        return (
            "这个公开视频让我想到，表达背后往往还有没有被说出的情绪。",
            None,
        )
    return ("留言已收下，会留到下一个合法时段再考虑回应。", None)
