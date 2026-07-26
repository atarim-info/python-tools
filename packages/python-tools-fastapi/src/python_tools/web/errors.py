"""Standard error envelope and shared error codes (PT-07 T7.1)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from fastapi import HTTPException


class ErrorCode(StrEnum):
    UNAUTHORIZED = "unauthorized"
    FORBIDDEN = "forbidden"
    NOT_FOUND = "not_found"
    CONFLICT = "conflict"
    CONFLICT_ETAG = "conflict_etag"
    SENT_LOCKED = "sent_locked"
    LIMIT_EXCEEDED = "limit_exceeded"
    VALIDATION_FAILED = "validation_failed"
    JOB_FAILED = "job_failed"
    INTERNAL = "internal"


# String constants for consumers that prefer bare imports (cv-service shim parity).
UNAUTHORIZED = ErrorCode.UNAUTHORIZED.value
FORBIDDEN = ErrorCode.FORBIDDEN.value
NOT_FOUND = ErrorCode.NOT_FOUND.value
CONFLICT = ErrorCode.CONFLICT.value
CONFLICT_ETAG = ErrorCode.CONFLICT_ETAG.value
SENT_LOCKED = ErrorCode.SENT_LOCKED.value
LIMIT_EXCEEDED = ErrorCode.LIMIT_EXCEEDED.value
VALIDATION_FAILED = ErrorCode.VALIDATION_FAILED.value
JOB_FAILED = ErrorCode.JOB_FAILED.value


def error_body(
    code: str,
    message: str,
    *,
    request_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build ``{"error": {"code", "message", "details"}}`` (+ optional request_id)."""
    err: dict[str, Any] = {"code": code, "message": message, "details": details or {}}
    if request_id is not None:
        err["request_id"] = request_id
    return {"error": err}


def api_error(
    status_code: int,
    code: str,
    message: str,
    **details: Any,
) -> HTTPException:
    """Raise-friendly helper: ``raise api_error(404, NOT_FOUND, "missing")``."""
    return HTTPException(
        status_code=status_code,
        detail={"code": code, "message": message, "details": details},
    )
