"""Pluggable health checks backing ``/healthz`` (liveness) and ``/readyz`` (readiness)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

# A check returns True when healthy. Raising is treated as unhealthy.
HealthCheck = Callable[[], bool]


@dataclass(frozen=True)
class CheckResult:
    name: str
    healthy: bool
    detail: str | None = None


@dataclass
class ReadinessReport:
    ready: bool
    checks: list[CheckResult] = field(default_factory=list)

    def as_dict(self) -> dict[str, object]:
        return {
            "status": "ready" if self.ready else "not_ready",
            "checks": [
                {"name": c.name, "healthy": c.healthy, "detail": c.detail} for c in self.checks
            ],
        }


class HealthRegistry:
    """Holds readiness checks keyed by name.

    Liveness is always trivially healthy (the process is running); readiness runs the
    registered dependency checks and fails closed if any check raises or returns False.
    """

    def __init__(self) -> None:
        self._checks: dict[str, HealthCheck] = {}

    def register(self, name: str, check: HealthCheck) -> None:
        self._checks[name] = check

    def liveness(self) -> dict[str, str]:
        return {"status": "ok"}

    def readiness(self) -> ReadinessReport:
        results: list[CheckResult] = []
        ready = True
        for name, check in self._checks.items():
            try:
                healthy = check()
                results.append(CheckResult(name=name, healthy=healthy))
            except Exception as exc:  # fail closed and report the reason
                healthy = False
                results.append(CheckResult(name=name, healthy=False, detail=str(exc)))
            ready = ready and healthy
        return ReadinessReport(ready=ready, checks=results)
