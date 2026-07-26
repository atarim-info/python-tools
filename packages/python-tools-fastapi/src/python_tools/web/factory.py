"""App factory that wires logging, observability, health, and error envelope."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from python_tools.config import BaseServiceSettings
from python_tools.logging import configure_logging, get_request_id
from python_tools.obs import HealthRegistry, setup_observability
from python_tools.web.errors import VALIDATION_FAILED, ErrorCode, error_body
from python_tools.web.etag import EtagMismatch
from python_tools.web.health import build_health_router
from python_tools.web.middleware import RequestContextMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

ExceptionMapping = tuple[type[Exception], int, str]


def _request_id(request: Request) -> str:
    state_id = getattr(request.state, "request_id", None)
    if state_id:
        return str(state_id)
    return request.headers.get("X-Request-ID") or get_request_id() or "-"


def install_error_handlers(
    app: FastAPI,
    exception_map: Sequence[ExceptionMapping] | None = None,
) -> None:
    """Map domain/storage exceptions to the standard error envelope."""
    mappings: list[ExceptionMapping] = [
        (EtagMismatch, 412, ErrorCode.CONFLICT_ETAG.value),
        *(exception_map or ()),
    ]

    for exc_type, status_code, code in mappings:

        async def handler(
            request: Request,
            exc: Exception,
            _status: int = status_code,
            _code: str = code,
        ) -> JSONResponse:
            return JSONResponse(
                status_code=_status,
                content=error_body(_code, str(exc) or _code, request_id=_request_id(request)),
            )

        app.add_exception_handler(exc_type, handler)

    @app.exception_handler(StarletteHTTPException)
    async def http_exc_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        request_id = _request_id(request)
        detail = exc.detail
        if isinstance(detail, dict) and "code" in detail:
            body = {"error": {**detail, "request_id": request_id}}
            if "details" not in body["error"]:
                body["error"]["details"] = {}
            return JSONResponse(status_code=exc.status_code, content=body)
        return JSONResponse(
            status_code=exc.status_code,
            content=error_body(
                f"http_{exc.status_code}",
                str(detail),
                request_id=request_id,
            ),
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exc_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        body = error_body(
            VALIDATION_FAILED,
            "request validation failed",
            request_id=_request_id(request),
        )
        body["detail"] = jsonable_encoder(exc.errors())
        return JSONResponse(status_code=422, content=body)


def create_app(
    *,
    title: str,
    version: str = "0.1.0",
    settings: BaseServiceSettings | None = None,
    health_registry: HealthRegistry | None = None,
    exception_map: Sequence[ExceptionMapping] | None = None,
    setup_logging: bool = True,
    setup_otel: bool = False,
    include_health_routes: bool = True,
    lifespan: Any = None,
) -> FastAPI:
    """One-call FastAPI bootstrap for python-tools consumers.

    Wires structured logging, optional OTel, request-ID middleware, the standard
    error envelope, and ``/healthz`` ``/readyz`` ``/metrics``.
    """
    if settings is not None and setup_logging:
        configure_logging(settings)
    if settings is not None and setup_otel:
        setup_observability(settings, enabled=True)

    app = FastAPI(title=title, version=version, lifespan=lifespan)
    if settings is not None:
        app.state.settings = settings

    health = health_registry or HealthRegistry()
    app.state.health_registry = health

    app.add_middleware(RequestContextMiddleware)
    install_error_handlers(app, exception_map)

    if include_health_routes:
        app.include_router(build_health_router(health, version=version))

    return app
