"""Structured logging for python-tools consumers.

structlog-based JSON logging (human-readable in dev) with PII masking, correlation /
request IDs, and OpenTelemetry trace/span-ID injection.
"""

from __future__ import annotations

from python_tools.logging.context import (
    bind_correlation_id,
    bind_request_id,
    clear_context,
    get_correlation_id,
    get_request_id,
)
from python_tools.logging.masking import mask_pii
from python_tools.logging.setup import configure_logging, get_logger

__all__ = [
    "bind_correlation_id",
    "bind_request_id",
    "clear_context",
    "configure_logging",
    "get_correlation_id",
    "get_logger",
    "get_request_id",
    "mask_pii",
]

__version__ = "0.1.0"
