"""``/healthz``, ``/readyz``, ``/metrics`` routes (closes PT-08 T8.2)."""

from __future__ import annotations

from fastapi import APIRouter, Response, status
from prometheus_client import CONTENT_TYPE_LATEST
from python_tools.obs import HealthRegistry, render_metrics


def build_health_router(
    health: HealthRegistry,
    *,
    version: str | None = None,
    include_metrics: bool = True,
) -> APIRouter:
    router = APIRouter(tags=["health"])

    @router.get("/healthz")
    async def healthz() -> dict[str, str]:
        body = health.liveness()
        if version is not None:
            body = {**body, "version": version}
        return body

    @router.get("/readyz")
    async def readyz(response: Response) -> dict[str, object]:
        report = health.readiness()
        if not report.ready:
            response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return report.as_dict()

    if include_metrics:

        @router.get("/metrics")
        async def metrics() -> Response:
            return Response(content=render_metrics(), media_type=CONTENT_TYPE_LATEST)

    return router
