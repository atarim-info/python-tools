"""Correlation / request ID context and OpenTelemetry trace injection."""

from __future__ import annotations

import contextvars
from typing import Any

_correlation_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "python_tools_correlation_id", default=None
)
_request_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "python_tools_request_id", default=None
)


def bind_correlation_id(value: str) -> None:
    """Set the correlation ID for the current context."""
    _correlation_id.set(value)


def bind_request_id(value: str) -> None:
    """Set the request ID for the current context."""
    _request_id.set(value)


def get_correlation_id() -> str | None:
    return _correlation_id.get()


def get_request_id() -> str | None:
    return _request_id.get()


def clear_context() -> None:
    """Reset correlation and request IDs (useful between test cases)."""
    _correlation_id.set(None)
    _request_id.set(None)


def add_ids(logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """structlog processor: attach correlation and request IDs when present."""
    cid = _correlation_id.get()
    if cid is not None:
        event_dict.setdefault("correlation_id", cid)
    rid = _request_id.get()
    if rid is not None:
        event_dict.setdefault("request_id", rid)
    return event_dict


def add_trace_context(logger: Any, method_name: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """structlog processor: attach OTel trace/span IDs if a span is active.

    OpenTelemetry is an optional dependency; when it is not installed this is a no-op.
    """
    try:
        from opentelemetry import trace
    except ImportError:
        return event_dict

    span = trace.get_current_span()
    ctx = span.get_span_context()
    if ctx is not None and ctx.is_valid:
        event_dict["trace_id"] = format(ctx.trace_id, "032x")
        event_dict["span_id"] = format(ctx.span_id, "016x")
    return event_dict
