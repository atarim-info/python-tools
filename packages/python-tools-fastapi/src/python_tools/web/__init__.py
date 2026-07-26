"""FastAPI conventions for python-tools consumers (PT-07).

Import root ``python_tools.web`` (distribution ``python-tools-fastapi``).
"""

from __future__ import annotations

from python_tools.web.errors import (
    CONFLICT,
    CONFLICT_ETAG,
    FORBIDDEN,
    JOB_FAILED,
    LIMIT_EXCEEDED,
    NOT_FOUND,
    SENT_LOCKED,
    UNAUTHORIZED,
    VALIDATION_FAILED,
    ErrorCode,
    api_error,
    error_body,
)
from python_tools.web.etag import EtagMismatch, check_if_match, make_etag
from python_tools.web.factory import create_app, install_error_handlers
from python_tools.web.health import build_health_router
from python_tools.web.idempotency import extract_idempotency_key
from python_tools.web.middleware import RequestContextMiddleware
from python_tools.web.pagination import Page, paginate

__all__ = [
    "CONFLICT",
    "CONFLICT_ETAG",
    "FORBIDDEN",
    "JOB_FAILED",
    "LIMIT_EXCEEDED",
    "NOT_FOUND",
    "SENT_LOCKED",
    "UNAUTHORIZED",
    "VALIDATION_FAILED",
    "ErrorCode",
    "EtagMismatch",
    "Page",
    "RequestContextMiddleware",
    "api_error",
    "build_health_router",
    "check_if_match",
    "create_app",
    "error_body",
    "extract_idempotency_key",
    "install_error_handlers",
    "make_etag",
    "paginate",
]

__version__ = "0.1.0"
