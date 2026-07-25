"""Prometheus metrics helpers.

A dedicated registry is exposed (rather than the global default) so services stay in
control of what they publish. No HTTP server is started here — the web package wires
``/metrics`` to :func:`render_metrics`.
"""

from __future__ import annotations

from prometheus_client import CollectorRegistry, generate_latest

_registry = CollectorRegistry()


def metrics_registry() -> CollectorRegistry:
    """Return the process-wide python-tools metrics registry."""
    return _registry


def render_metrics() -> bytes:
    """Render the current metrics in Prometheus text exposition format."""
    return generate_latest(_registry)
