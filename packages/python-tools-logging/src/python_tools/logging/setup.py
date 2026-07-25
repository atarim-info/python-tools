"""Logging configuration entry points."""

from __future__ import annotations

import logging as std_logging
from typing import Any

import structlog
from python_tools.config import BaseServiceSettings, Environment
from python_tools.logging.context import add_ids, add_trace_context
from python_tools.logging.masking import mask_pii


def _resolve_level(name: str) -> int:
    return std_logging.getLevelNamesMapping().get(name.upper(), std_logging.INFO)


def configure_logging(settings: BaseServiceSettings, *, json_logs: bool | None = None) -> None:
    """Configure structlog for the process.

    JSON output by default; a human-readable console renderer in the ``dev``
    environment. Pass ``json_logs`` to force one or the other.
    """

    use_json = json_logs if json_logs is not None else settings.environment is not Environment.DEV

    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        add_ids,
        add_trace_context,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        mask_pii,
    ]
    if use_json:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(_resolve_level(settings.log_level)),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str | None = None) -> Any:
    """Return a bound structlog logger."""
    return structlog.get_logger(name)
