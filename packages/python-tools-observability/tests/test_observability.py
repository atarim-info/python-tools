from __future__ import annotations

from python_tools.config import BaseServiceSettings
from python_tools.obs import HealthRegistry, render_metrics, setup_observability


def test_setup_noop_by_default() -> None:
    settings = BaseServiceSettings(service_name="svc")
    obs = setup_observability(settings)
    assert obs.enabled is False
    tracer = obs.get_tracer("t")
    with tracer.start_as_current_span("unit") as span:
        assert span is not None


def test_liveness_ok() -> None:
    assert HealthRegistry().liveness() == {"status": "ok"}


def test_readiness_all_healthy() -> None:
    reg = HealthRegistry()
    reg.register("db", lambda: True)
    reg.register("cache", lambda: True)
    report = reg.readiness()
    assert report.ready is True
    assert len(report.checks) == 2


def test_readiness_fails_closed_on_exception() -> None:
    reg = HealthRegistry()

    def boom() -> bool:
        raise RuntimeError("down")

    reg.register("db", boom)
    report = reg.readiness()
    assert report.ready is False
    assert report.checks[0].detail == "down"


def test_render_metrics_returns_bytes() -> None:
    assert isinstance(render_metrics(), bytes)
