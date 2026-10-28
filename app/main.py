"""B6 本地 FastAPI 应用与公开投影。"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api_models import (
    AgentResponse,
    APIErrorDetail,
    APIErrorResponse,
    ChatRequest,
    ChatResponse,
    HealthResponse,
    MemoryResponse,
    ReadyResponse,
    TimelineResponse,
    WorldResponse,
)
from app.db import database_ready
from app.local_state import LocalWorldStore, PublicProjectionError

APP_NAME = "AI World"
APP_VERSION = "0.1.0"
PUBLIC_API_VERSION = "v1"
WEB_ROOT = Path(__file__).resolve().parents[1] / "web"


def create_app(
    *,
    store: LocalWorldStore | None = None,
    readiness_check: Callable[[], Awaitable[bool]] | None = None,
) -> FastAPI:
    local_world = store or LocalWorldStore()
    application = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url=None,
    )
    application.openapi_version = "3.1.0"
    application.state.local_world = local_world
    application.state.readiness_check = readiness_check

    @application.middleware("http")
    async def public_api_headers(request: Request, call_next):
        request.state.request_id = str(uuid.uuid4())
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        return response

    @application.exception_handler(PublicProjectionError)
    async def projection_error_handler(
        request: Request,
        error: PublicProjectionError,
    ) -> JSONResponse:
        return _error_response(
            request,
            status_code=error.status_code,
            code=error.code,
            message=str(error),
        )

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request: Request,
        error: RequestValidationError,
    ) -> JSONResponse:
        safe_details = [
            {
                "location": [str(part) for part in item.get("loc", ())],
                "reason": item.get("type", "invalid_request"),
            }
            for item in error.errors()
        ]
        return _error_response(
            request,
            status_code=422,
            code="invalid_request",
            message="请求字段不符合公开 API 契约",
            details=safe_details,
        )

    @application.exception_handler(HTTPException)
    async def http_error_handler(
        request: Request,
        error: HTTPException,
    ) -> JSONResponse:
        code = "not_found" if error.status_code == 404 else "http_error"
        return _error_response(
            request,
            status_code=error.status_code,
            code=code,
            message="请求无法处理",
        )

    @application.get(
        "/health",
        response_model=HealthResponse,
        operation_id="getHealth",
        tags=["system"],
    )
    async def health() -> HealthResponse:
        """Liveness is independent from database readiness."""
        return HealthResponse(
            status="ok",
            service="ai-world",
            version=APP_VERSION,
        )

    @application.get(
        "/ready",
        response_model=ReadyResponse,
        operation_id="getReadiness",
        tags=["system"],
        responses={503: {"model": APIErrorResponse}},
    )
    async def ready() -> ReadyResponse:
        check = application.state.readiness_check or database_ready
        try:
            available = await check()
        except Exception:
            available = False
        if not available:
            raise PublicProjectionError(
                "database_unavailable",
                "数据库当前不可用",
                status_code=503,
            )
        return ReadyResponse(status="ready", service="ai-world")

    @application.get(
        "/world",
        response_model=WorldResponse,
        operation_id="getWorld",
        tags=["world"],
    )
    async def get_world() -> WorldResponse:
        return local_world.world()

    @application.get(
        "/agent",
        response_model=AgentResponse,
        operation_id="getAgent",
        tags=["world"],
        responses={404: {"model": APIErrorResponse}},
    )
    async def get_agent(
        person_id: str = Query(default="char_lin_cheng"),
    ) -> AgentResponse:
        return local_world.agent(person_id)

    @application.get(
        "/timeline",
        response_model=TimelineResponse,
        operation_id="getTimeline",
        tags=["world"],
        responses={400: {"model": APIErrorResponse}},
    )
    async def get_timeline(
        cursor: str | None = Query(default=None),
        limit: int = Query(default=20, ge=1, le=50),
    ) -> TimelineResponse:
        return local_world.timeline(cursor=cursor, limit=limit)

    @application.get(
        "/memory",
        response_model=MemoryResponse,
        operation_id="getMemory",
        tags=["memory"],
    )
    async def get_memory(
        kind: Literal["经历", "回顾", "关系", "偏好"] | None = Query(
            default=None
        ),
        limit: int = Query(default=20, ge=1, le=50),
    ) -> MemoryResponse:
        return local_world.memory(kind=kind, limit=limit)

    @application.post(
        "/chat",
        response_model=ChatResponse,
        operation_id="sendObserverMessage",
        tags=["chat"],
        responses={422: {"model": APIErrorResponse}},
    )
    async def send_chat(body: ChatRequest) -> ChatResponse:
        return local_world.chat(body.message)

    if WEB_ROOT.is_dir():
        application.mount(
            "/static",
            StaticFiles(directory=WEB_ROOT),
            name="static",
        )

        @application.get("/", include_in_schema=False)
        async def web_index() -> FileResponse:
            return FileResponse(WEB_ROOT / "index.html")

    return application


def _error_response(
    request: Request,
    *,
    status_code: int,
    code: str,
    message: str,
    details: list[dict] | None = None,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    payload = APIErrorResponse(
        schema_version="rpg-error-v1",
        error=APIErrorDetail(
            code=code,
            message=message,
            request_id=request_id,
        ),
    ).model_dump()
    if details:
        payload["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=payload)


app = create_app()
