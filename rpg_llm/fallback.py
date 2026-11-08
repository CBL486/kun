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
    if request.template_id == "study_reflection":
        return (
            "今天的学习让我更愿意先听清楚，再理解自己的感受与边界。",
            None,
        )
    if request.template_id == "media_observation":
        return (
            "这个公开视频让我想到，表达背后往往还有没有被说出的情绪。",
            None,
        )
    if request.template_id == "persona_reply":
        return (
            "我听见了。让我先按自己的方式想一想，再认真回答你。",
            None,
        )
    return ("当前暂不能生成新的表达，继续使用安全规则。", None)
