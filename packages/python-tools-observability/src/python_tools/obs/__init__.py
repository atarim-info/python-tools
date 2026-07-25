"""Observability bootstrap for python-tools consumers.

OpenTelemetry tracer/meter setup (no-op by default for tests and CLIs), a pluggable
health-check registry for ``/healthz`` + ``/readyz``, and a Prometheus metrics helper.
"""

from __future__ import annotations

from python_tools.obs.health import (
    CheckResult,
    HealthCheck,
    HealthRegistry,
    ReadinessReport,
)
from python_tools.obs.metrics import metrics_registry, render_metrics
from python_tools.obs.setup import Observability, setup_observability

__all__ = [
    "CheckResult",
    "HealthCheck",
    "HealthRegistry",
    "Observability",
    "ReadinessReport",
    "metrics_registry",
    "render_metrics",
    "setup_observability",
]

__version__ = "0.1.0"
