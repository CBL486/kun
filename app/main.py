"""B6 本地 FastAPI 应用与公开投影。"""

from __future__ import annotations

import uuid
import time
from collections.abc import Awaitable, Callable
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.responses import FileResponse
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles

from app.api_models import (
    AgentResponse,
    APIErrorDetail,
    APIErrorResponse,
    ChatRequest,
    ChatResponse,
    DeepSeekKeyRequest,
    HealthResponse,
    PersonaBaselineInput,
    PersonaBaselineView,
    PersonaResponse,
    PersonaStateView,
    PersonaStatusResponse,
    ReadyResponse,
    SetupCompleteRequest,
    SetupStatusResponse,
    SetupValidationResponse,
    TimelineResponse,
    WorldResponse,
)
from app.db import database_ready
from app.local_state import LocalWorldStore, PublicProjectionError
from app.metrics import MetricsRegistry
from app.persona import DatabasePersonaStore, PersonaError, PersonaStore
from app.school import SchoolAutonomyService
from app.settings import settings
from app.setup import DeepSeekSetupStore, DeepSeekValidator, SetupError
from app.self_awareness import SelfAwarenessService
from app.world_clock import WorldClockStore
from rpg_orm.migrations import create_database_engine
from rpg_orm.product_repository import ProductRepository
from rpg_scheduler import PersistentMessageQueue, SchedulerRepository

APP_NAME = "AI World"
APP_VERSION = "0.1.0"
PUBLIC_API_VERSION = "v2"
WEB_ROOT = Path(__file__).resolve().parents[1] / "web"
ASSET_ROOT = Path(__file__).resolve().parents[1] / "assets"


def create_app(
    *,
    store: LocalWorldStore | None = None,
    message_store: PersistentMessageQueue | None = None,
    readiness_check: Callable[[], Awaitable[bool]] | None = None,
    setup_store: DeepSeekSetupStore | None = None,
    setup_validator: DeepSeekValidator | None = None,
    persona_store: PersonaStore | None = None,
    setup_gate: bool = False,
) -> FastAPI:
    if store is None and message_store is None:
        if settings.scheduler_database_url:
            message_store = PersistentMessageQueue(
                create_database_engine(settings.scheduler_database_url)
            )
    local_setup = setup_store or DeepSeekSetupStore.from_settings(settings)
    local_validator = setup_validator or DeepSeekValidator()
    if persona_store is not None:
        local_persona = persona_store
    elif setup_gate:
        product_url = (
            settings.product_database_url
            or settings.scheduler_database_url
            or "sqlite:///./data/local.sqlite3"
        )
        product_repository = ProductRepository(
            create_database_engine(product_url)
        )
        local_persona = DatabasePersonaStore(product_repository)
        legacy_json = (
            Path(settings.persona_directory)
            if settings.persona_directory
            else Path.cwd() / "data" / "persona"
        ) / "persona.json"
        if local_persona.get() is None and legacy_json.is_file():
            product_repository.migrate_persona_json(legacy_json)
    else:
        local_persona = PersonaStore.from_settings(settings)
    local_self_awareness = None
    local_school = None
    if isinstance(local_persona, DatabasePersonaStore):
        local_self_awareness = SelfAwarenessService(
            local_persona.repository,
        )
        local_school = SchoolAutonomyService(local_persona.repository)
    local_world = store or LocalWorldStore(
        message_store=message_store,
        persona_store=local_persona,
        world_clock_store=WorldClockStore.from_settings(settings),
        self_awareness_service=local_self_awareness,
        school_service=local_school,
    )
    application = FastAPI(
        title=APP_NAME,
        version=APP_VERSION,
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url=None,
    )
    application.openapi_version = "3.1.0"
    application.state.local_world = local_world
    application.state.message_store = message_store
    application.state.readiness_check = readiness_check
    application.state.metrics = MetricsRegistry()
    application.state.setup_store = local_setup
    application.state.setup_validator = local_validator
    application.state.persona_store = local_persona
    application.state.self_awareness = local_self_awareness
    application.state.school_autonomy = local_school

    def combined_setup_status() -> SetupStatusResponse:
        setup_status = local_setup.status()
        persona_status = local_persona.status()
        return SetupStatusResponse(
            configured=setup_status.configured,
            provider=setup_status.provider,
            key_hint=setup_status.key_hint,
            persona_configured=persona_status["configured"],
            world_ready=bool(
                setup_status.configured
                and setup_status.world_ready
                and persona_status["configured"]
            ),
        )

    @application.middleware("http")
    async def public_api_headers(request: Request, call_next):
        request.state.request_id = str(uuid.uuid4())
        started = time.perf_counter()
        protected_paths = {"/world", "/agent", "/timeline", "/chat"}
        path = request.url.path.rstrip("/") or "/"
        if setup_gate and path in protected_paths:
            setup_status = combined_setup_status()
            if not setup_status.world_ready:
                response = _error_response(
                    request,
                    status_code=409,
                    code="setup_required",
                    message="请先完成 DeepSeek Key 和人设设置",
                )
                application.state.metrics.observe(
                    status_code=response.status_code,
                    duration_seconds=time.perf_counter() - started,
                )
                response.headers["X-Request-ID"] = request.state.request_id
                response.headers["X-Content-Type-Options"] = "nosniff"
                response.headers["Cache-Control"] = "no-store"
                return response
        response = await call_next(request)
        application.state.metrics.observe(
            status_code=response.status_code,
            duration_seconds=time.perf_counter() - started,
        )
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Cache-Control"] = "no-store"
        return response

    @application.get("/metrics", include_in_schema=False)
    async def metrics() -> PlainTextResponse:
        check = application.state.readiness_check or database_ready
        try:
            database = await check()
        except Exception:
            database = False
        scheduler_backlog = None
        if message_store is not None:
            try:
                scheduler_backlog = SchedulerRepository(
                    message_store.engine,
                    migrate_schema=False,
                ).backlog(now=datetime.now(timezone.utc))
            except Exception:
                scheduler_backlog = None
        backup_age_seconds = None
        if settings.backup_directory:
            try:
                backup_files = [
                    path
                    for path in Path(settings.backup_directory).glob("aiworld-*")
                    if path.is_file()
                ]
                if backup_files:
                    newest = max(
                        backup_files,
                        key=lambda path: path.stat().st_mtime,
                    )
                    backup_age_seconds = max(
                        0.0,
                        time.time() - newest.stat().st_mtime,
                    )
            except OSError:
                backup_age_seconds = None
        return PlainTextResponse(
            application.state.metrics.render(
                version=APP_VERSION,
                database_ready=database,
                scheduler_backlog=scheduler_backlog,
                backup_age_seconds=backup_age_seconds,
            ),
            media_type="text/plain; version=0.0.4",
        )

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

    @application.exception_handler(SetupError)
    async def setup_error_handler(
        request: Request,
        error: SetupError,
    ) -> JSONResponse:
        return _error_response(
            request,
            status_code=error.status_code,
            code=error.code,
            message=str(error),
        )

    @application.exception_handler(PersonaError)
    async def persona_error_handler(
        request: Request,
        error: PersonaError,
    ) -> JSONResponse:
        return _error_response(
            request,
            status_code=error.status_code,
            code=error.code,
            message=str(error),
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
        "/api/setup/status",
        response_model=SetupStatusResponse,
        operation_id="getSetupStatus",
        tags=["setup"],
    )
    async def get_setup_status() -> SetupStatusResponse:
        return combined_setup_status()

    @application.post(
        "/api/setup/deepseek/validate",
        response_model=SetupValidationResponse,
        operation_id="validateDeepSeekKey",
        tags=["setup"],
    )
    async def validate_deepseek_key(
        body: DeepSeekKeyRequest,
    ) -> SetupValidationResponse:
        local_setup.validate_key(
            body.api_key.get_secret_value(),
            local_validator,
        )
        return SetupValidationResponse(valid=True, provider="deepseek")

    @application.post(
        "/api/setup/deepseek/save",
        response_model=SetupStatusResponse,
        operation_id="saveDeepSeekKey",
        tags=["setup"],
    )
    async def save_deepseek_key(
        body: DeepSeekKeyRequest,
    ) -> SetupStatusResponse:
        status = local_setup.save_key(
            body.api_key.get_secret_value(),
            local_validator,
        )
        return SetupStatusResponse(
            configured=status.configured,
            provider=status.provider,
            key_hint=status.key_hint,
            persona_configured=local_persona.status()["configured"],
            world_ready=False,
        )

    @application.post(
        "/api/setup/complete",
        response_model=SetupStatusResponse,
        operation_id="completeSetup",
        tags=["setup"],
    )
    async def complete_setup(
        body: SetupCompleteRequest,
    ) -> SetupStatusResponse:
        local_setup.complete(
            persona_configured=local_persona.status()["configured"],
        )
        return combined_setup_status()

    @application.post(
        "/api/setup/deepseek/clear",
        response_model=SetupStatusResponse,
        operation_id="clearDeepSeekKey",
        tags=["setup"],
    )
    async def clear_deepseek_key() -> SetupStatusResponse:
        local_setup.clear_key()
        return combined_setup_status()

    @application.get(
        "/api/persona/status",
        response_model=PersonaStatusResponse,
        operation_id="getPersonaStatus",
        tags=["persona"],
    )
    async def get_persona_status() -> PersonaStatusResponse:
        return PersonaStatusResponse(**local_persona.status())

    @application.get(
        "/api/persona",
        response_model=PersonaResponse,
        operation_id="getPersona",
        tags=["persona"],
        responses={404: {"model": APIErrorResponse}},
    )
    async def get_persona() -> PersonaResponse:
        return _persona_response(local_persona)

    @application.post(
        "/api/persona/default",
        response_model=PersonaResponse,
        operation_id="useDefaultPersona",
        tags=["persona"],
    )
    async def use_default_persona() -> PersonaResponse:
        local_persona.use_default()
        return _persona_response(local_persona)

    @application.put(
        "/api/persona/baseline",
        response_model=PersonaResponse,
        operation_id="replacePersonaBaseline",
        tags=["persona"],
    )
    async def replace_persona_baseline(
        body: PersonaBaselineInput,
    ) -> PersonaResponse:
        local_persona.save_custom(body.model_dump())
        return _persona_response(local_persona)

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
            if setup_gate and not combined_setup_status().world_ready:
                return FileResponse(WEB_ROOT / "setup.html")
            return FileResponse(WEB_ROOT / "index.html")

        @application.get("/setup", include_in_schema=False)
        async def setup_page() -> FileResponse:
            return FileResponse(WEB_ROOT / "setup.html")

    if ASSET_ROOT.is_dir():
        application.mount(
            "/assets",
            StaticFiles(directory=ASSET_ROOT),
            name="assets",
        )

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


app = create_app(setup_gate=True)


def _persona_response(persona_store: PersonaStore) -> PersonaResponse:
    bundle = persona_store.get()
    if not bundle:
        raise PersonaError(
            "persona_not_configured",
            "尚未配置角色人设",
            status_code=404,
        )
    return PersonaResponse(
        schema_version="rpg-persona-v1",
        baseline_revision=bundle["baseline_revision"],
        baseline=PersonaBaselineView(**bundle["baseline"]),
        state=PersonaStateView(**bundle["state"]),
    )
