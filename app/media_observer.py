"""Controlled observation of public Douyin and Bilibili metadata."""

from __future__ import annotations

import hashlib
import html
import re
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from html.parser import HTMLParser
from typing import Any, Protocol
from urllib.parse import urlsplit, urlunsplit
from zoneinfo import ZoneInfo

import httpx

from rpg_llm.models import LlmRequest
from rpg_llm.review import MockReviewAdapter, ReviewAdapter
from rpg_sim.ids import stable_id
from rpg_storage.errors import StorageError


WORLD_ID = "world_qinghe_v1"
CHARACTER_ID = "char_lin_cheng"
WORLD_TIMEZONE = ZoneInfo("Asia/Shanghai")
ALLOWED_HOSTS = {
    "bilibili": {"bilibili.com", "www.bilibili.com", "b23.tv"},
    "douyin": {"douyin.com", "www.douyin.com", "v.douyin.com"},
}
MAX_PAGE_BYTES = 512_000


class MediaObservationError(StorageError):
    pass


@dataclass(frozen=True)
class PublicMetadata:
    provider: str
    canonical_url: str
    title: str
    description: str
    cover_url: str | None = None


@dataclass(frozen=True)
class MediaSummary:
    text: str
    input_tokens: int
    output_tokens: int
    provider: str
    model: str


class MediaFetcher(Protocol):
    def fetch(self, provider: str, url: str) -> PublicMetadata: ...


class MediaSummarizer(Protocol):
    def summarize(
        self,
        *,
        metadata: PublicMetadata,
        token_budget: int,
        operation_id: str,
        budget_date: str,
    ) -> MediaSummary: ...


class _OpenGraphParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.values: dict[str, str] = {}
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag: str, attrs):
        attributes = dict(attrs)
        if tag == "title":
            self._in_title = True
        if tag == "meta":
            key = attributes.get("property") or attributes.get("name")
            content = attributes.get("content")
            if key and content:
                self.values[key.casefold()] = content.strip()

    def handle_endtag(self, tag: str):
        if tag == "title":
            self._in_title = False

    def handle_data(self, data: str):
        if self._in_title:
            self.title += data


class HttpPublicMediaFetcher:
    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        timeout_seconds: float = 15.0,
    ):
        self.client = client or httpx.Client(
            timeout=timeout_seconds,
            follow_redirects=True,
        )

    def fetch(self, provider: str, url: str) -> PublicMetadata:
        canonical = canonical_public_url(provider, url)
        try:
            response = self.client.get(
                url,
                headers={
                    "User-Agent": "AIWorld-PublicObserver/1.0",
                    "Accept": "text/html,application/xhtml+xml",
                },
            )
        except httpx.HTTPError as error:
            raise MediaObservationError(
                "media_network_error",
                "无法读取公开媒体页面",
            ) from error
        final_url = str(response.url)
        final_canonical = canonical_public_url(provider, final_url)
        if response.status_code in {401, 403}:
            raise MediaObservationError(
                "media_access_denied",
                "该内容不是公开可访问内容",
            )
        if response.status_code >= 400:
            raise MediaObservationError(
                "media_http_error",
                "公开媒体页面读取失败",
            )
        content = response.content
        if len(content) > MAX_PAGE_BYTES:
            raise MediaObservationError(
                "media_response_too_large",
                "公开媒体页面超过允许大小",
            )
        parser = _OpenGraphParser()
        parser.feed(content.decode("utf-8", errors="replace"))
        title = _clean_text(
            parser.values.get("og:title") or parser.title or "公开视频"
        )
        description = _clean_text(
            parser.values.get("og:description")
            or parser.values.get("description")
            or ""
        )
        if not title:
            raise MediaObservationError(
                "media_metadata_missing",
                "公开视频缺少可读标题",
            )
        return PublicMetadata(
            provider=provider,
            canonical_url=final_canonical,
            title=title[:240],
            description=description[:1_000],
            cover_url=_safe_cover_url(parser.values.get("og:image")),
        )

    def fetch_bilibili_hot(self, *, limit: int = 10) -> list[PublicMetadata]:
        if not 1 <= limit <= 20:
            raise MediaObservationError(
                "invalid_hot_limit",
                "热门列表数量必须在 1 至 20",
            )
        try:
            response = self.client.get(
                "https://api.bilibili.com/x/web-interface/popular",
                params={"ps": limit, "pn": 1},
            )
            payload = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise MediaObservationError(
                "media_hot_unavailable",
                "B站公开热门列表暂不可用",
            ) from error
        items = (
            payload.get("data", {}).get("list", [])
            if isinstance(payload, dict)
            else []
        )
        result = []
        for item in items[:limit]:
            bvid = item.get("bvid")
            if not bvid:
                continue
            result.append(
                PublicMetadata(
                    provider="bilibili",
                    canonical_url=f"https://www.bilibili.com/video/{bvid}",
                    title=_clean_text(str(item.get("title", "")))[:240],
                    description=_clean_text(
                        str(item.get("desc", ""))
                    )[:1_000],
                )
            )
        return result


class StaticMediaSummarizer:
    def summarize(
        self,
        *,
        metadata: PublicMetadata,
        token_budget: int,
        operation_id: str,
        budget_date: str,
    ) -> MediaSummary:
        text = (
            f"我看到的是一段关于“{metadata.title[:80]}”的公开视频。"
            "它让我想到，理解一段表达不只在于知道内容，也在于体会它为什么被说出来。"
        )
        return MediaSummary(
            text=text[:600],
            input_tokens=min(100, token_budget),
            output_tokens=min(max(0, token_budget - 100), 100),
            provider="local-static",
            model="media-static-v1",
        )


class GatewayMediaSummarizer:
    def __init__(self, gateway: Any):
        self.gateway = gateway

    def summarize(
        self,
        *,
        metadata: PublicMetadata,
        token_budget: int,
        operation_id: str,
        budget_date: str,
    ) -> MediaSummary:
        result = self.gateway.generate(
            LlmRequest(
                operation_id=operation_id,
                template_id="media_observation",
                variables={
                    "provider": metadata.provider,
                    "title": metadata.title,
                    "description": metadata.description,
                },
                budget_date=budget_date,
                max_output_tokens=min(240, token_budget),
                interface="media",
            )
        )
        text = result.get("text")
        usage = result.get("usage") or {}
        if not isinstance(text, str) or not text.strip():
            raise MediaObservationError(
                "media_summary_invalid",
                "视频摘要不可用",
            )
        return MediaSummary(
            text=text.strip()[:800],
            input_tokens=int(usage.get("input_tokens", 0)),
            output_tokens=int(usage.get("output_tokens", 0)),
            provider=str(result.get("provider") or "local-rule"),
            model=str(result.get("model") or "media-fallback-v1"),
        )


class MediaObservationService:
    def __init__(
        self,
        repository: Any,
        *,
        fetcher: MediaFetcher | None = None,
        summarizer: MediaSummarizer | None = None,
        reviewer: ReviewAdapter | None = None,
        world_id: str = WORLD_ID,
        character_id: str = CHARACTER_ID,
        daily_limit: int = 2,
        token_budget: int = 600,
    ):
        self.repository = repository
        self.fetcher = fetcher or HttpPublicMediaFetcher()
        self.summarizer = summarizer or StaticMediaSummarizer()
        self.reviewer = reviewer or MockReviewAdapter()
        self.world_id = world_id
        self.character_id = character_id
        self.daily_limit = daily_limit
        self.token_budget = token_budget

    def observe(
        self,
        *,
        provider: str,
        url: str,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        current = _local_time(now or datetime.now(WORLD_TIMEZONE))
        canonical = canonical_public_url(provider, url)
        url_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        existing = self.repository.get_media_observation(
            world_id=self.world_id,
            url_hash=url_hash,
        )
        if existing:
            return self._response(existing, replayed=True)
        start = datetime.combine(
            current.date(),
            time.min,
            tzinfo=WORLD_TIMEZONE,
        )
        observed_today = self.repository.count_media_observations_on_date(
            world_id=self.world_id,
            start_at=start.isoformat(),
            end_at=(start + timedelta(days=1)).isoformat(),
        )
        if observed_today >= self.daily_limit:
            raise MediaObservationError(
                "media_daily_limit",
                "今天已经达到视频观察上限",
            )
        observation_id = stable_id("media", [self.world_id, url_hash])
        observation = self.repository.create_media_observation(
            observation_id=observation_id,
            world_id=self.world_id,
            character_id=self.character_id,
            provider=provider,
            url_hash=url_hash,
            status="pending",
            summary="",
            emotional_valence=0.0,
            created_at=current.isoformat(),
        )
        try:
            metadata = self.fetcher.fetch(provider, canonical)
            metadata_review = self.reviewer.review(
                {
                    "title": metadata.title,
                    "description": metadata.description,
                },
                None,
            )
            if metadata_review.status != "approved":
                observation = self.repository.update_media_observation(
                    observation_id=observation_id,
                    status="blocked",
                    summary="",
                    emotional_valence=0.0,
                )
                return self._response(observation, blocked=True)
            summary = self.summarizer.summarize(
                metadata=metadata,
                token_budget=self.token_budget,
                operation_id=f"media:{observation_id}",
                budget_date=current.date().isoformat(),
            )
            if summary.input_tokens + summary.output_tokens > self.token_budget:
                summary = StaticMediaSummarizer().summarize(
                    metadata=metadata,
                    token_budget=self.token_budget,
                    operation_id=f"media:{observation_id}",
                    budget_date=current.date().isoformat(),
                )
            summary_review = self.reviewer.review(summary.text, None)
            if summary_review.status != "approved":
                observation = self.repository.update_media_observation(
                    observation_id=observation_id,
                    status="blocked",
                    summary="",
                    emotional_valence=0.0,
                )
                return self._response(observation, blocked=True)
            event_id = stable_id("evt", ["media", observation_id])
            valence = _estimate_valence(metadata.title + metadata.description)
            self.repository.record_memory_event(
                {
                    "event_id": event_id,
                    "world_id": self.world_id,
                    "actor_id": self.character_id,
                    "participants": [self.character_id],
                    "location_id": None,
                    "event_type": "media_observed",
                    "occurred_at": current.isoformat(),
                    "summary": summary.text,
                    "valence": valence,
                    "intensity": 0.2,
                    "importance": 0.3,
                    "confidence": 1.0,
                    "visibility": "private",
                    "source": "media",
                    "dedupe_key": (
                        f"media:{observation_id}:{self.character_id}"
                    ),
                    "metadata": {
                        "provider": provider,
                        "url_hash": url_hash,
                        "summary_provider": summary.provider,
                        "summary_model": summary.model,
                    },
                }
            )
            self.repository.update_emotion(
                event_id=event_id,
                world_id=self.world_id,
                character_id=self.character_id,
                values={"curiosity": 0.005},
                updated_at=current.isoformat(),
            )
            observation = self.repository.update_media_observation(
                observation_id=observation_id,
                status="reviewed",
                summary=summary.text,
                emotional_valence=valence,
                memory_event_id=event_id,
            )
            return self._response(observation, replayed=False)
        except Exception as error:
            self.repository.update_media_observation(
                observation_id=observation_id,
                status="failed",
                summary="",
                emotional_valence=0.0,
            )
            if isinstance(error, MediaObservationError):
                raise
            raise MediaObservationError(
                "media_observation_failed",
                "视频观察失败，未写入记忆",
            ) from error

    def observe_bilibili_hot(
        self,
        *,
        limit: int = 10,
        now: datetime | None = None,
    ) -> dict[str, Any]:
        fetch_hot = getattr(self.fetcher, "fetch_bilibili_hot", None)
        if fetch_hot is None:
            raise MediaObservationError(
                "media_hot_unavailable",
                "当前媒体适配器不支持公开热门列表",
            )
        for metadata in fetch_hot(limit=limit):
            if self.repository.get_media_observation(
                world_id=self.world_id,
                url_hash=hashlib.sha256(
                    metadata.canonical_url.encode("utf-8")
                ).hexdigest(),
            ):
                continue
            return self.observe(
                provider="bilibili",
                url=metadata.canonical_url,
                now=now,
            )
        raise MediaObservationError(
            "media_hot_exhausted",
            "公开热门列表中没有新的可观察视频",
        )

    @staticmethod
    def _response(
        observation: dict[str, Any],
        *,
        replayed: bool = False,
        blocked: bool = False,
    ) -> dict[str, Any]:
        return {
            "observation_id": observation["observation_id"],
            "status": observation["status"],
            "summary": observation["summary"],
            "emotional_valence": observation["emotional_valence"],
            "memory_event_id": observation["memory_event_id"],
            "blocked": blocked or observation["status"] == "blocked",
            "replayed": replayed,
        }


def canonical_public_url(provider: str, url: str) -> str:
    if provider not in ALLOWED_HOSTS:
        raise MediaObservationError(
            "unsupported_media_provider",
            "只支持 B站或抖音公开链接",
        )
    parsed = urlsplit(url)
    host = (parsed.hostname or "").casefold()
    if (
        parsed.scheme != "https"
        or host not in ALLOWED_HOSTS[provider]
        or parsed.username
        or parsed.password
        or parsed.port not in {None, 443}
    ):
        raise MediaObservationError(
            "unsupported_media_url",
            "只允许支持的平台公开 HTTPS 链接",
        )
    path = parsed.path or "/"
    if any(token in path.casefold() for token in ("/login", "/member", "/space")):
        raise MediaObservationError(
            "unsupported_media_url",
            "该链接不是支持的公开视频页面",
        )
    return urlunsplit(("https", host, path.rstrip("/") or "/", "", ""))


def _safe_cover_url(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlsplit(value)
    if parsed.scheme not in {"https", "http"} or not parsed.hostname:
        return None
    return value


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def _estimate_valence(text: str) -> float:
    lowered = text.casefold()
    negative = sum(
        word in lowered
        for word in ("悲伤", "告别", "痛苦", "失去", "难过")
    )
    positive = sum(
        word in lowered
        for word in ("温暖", "希望", "快乐", "成长", "治愈")
    )
    return round(max(-0.3, min(0.3, (positive - negative) * 0.1)), 3)


def _local_time(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=WORLD_TIMEZONE)
    return value.astimezone(WORLD_TIMEZONE)
