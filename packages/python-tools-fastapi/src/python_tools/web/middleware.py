"""Request-ID, access-log, and timing middleware (PT-07 T7.2)."""

from __future__ import annotations

import time
import uuid
from collections.abc import Awaitable, Callable

from python_tools.logging import bind_request_id, clear_context, get_logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Bind ``X-Request-ID``, log access, and echo the ID on the response."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        bind_request_id(request_id)
        request.state.request_id = request_id
        log = get_logger("access")
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            elapsed = time.perf_counter() - start
            log.exception(
                "request_failed",
                method=request.method,
                path=request.url.path,
                duration_ms=round(elapsed * 1000, 2),
            )
            clear_context()
            raise
        elapsed = time.perf_counter() - start
        response.headers["X-Request-ID"] = request_id
        log.info(
            "request",
            method=request.method,
            path=request.url.path,
            status=response.status_code,
            duration_ms=round(elapsed * 1000, 2),
        )
        clear_context()
        return response
