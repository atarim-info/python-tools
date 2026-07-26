"""Job store protocol (Mongo Wave 1; Postgres deferred)."""

from __future__ import annotations

from typing import Any, Protocol

from python_tools.jobs.models import AsyncJob


class JobStore(Protocol):
    async def create(
        self,
        user_id: str,
        kind: str,
        *,
        idempotency_key: str | None = None,
        payload: dict[str, Any] | None = None,
        max_attempts: int = 3,
    ) -> AsyncJob: ...

    async def get(self, user_id: str, job_id: str) -> AsyncJob | None: ...

    async def claim_next(self) -> AsyncJob | None: ...

    async def heartbeat(self, job_id: str) -> None: ...

    async def complete(self, job_id: str, result: dict[str, Any]) -> None: ...

    async def fail(self, job_id: str, error: str, *, retryable: bool = True) -> AsyncJob: ...
