"""In-memory job store for tests and hermetic local runs."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from python_tools.jobs.models import AsyncJob, JobStatus


def _now() -> str:
    return datetime.now(UTC).isoformat()


class InMemoryJobStore:
    """Implements :class:`~python_tools.jobs.protocol.JobStore` without Mongo."""

    def __init__(self) -> None:
        self._jobs: dict[str, AsyncJob] = {}

    async def create(
        self,
        user_id: str,
        kind: str,
        *,
        idempotency_key: str | None = None,
        payload: dict[str, Any] | None = None,
        max_attempts: int = 3,
    ) -> AsyncJob:
        if idempotency_key:
            for job in self._jobs.values():
                if job.user_id == user_id and job.idempotency_key == idempotency_key:
                    return job
        now = _now()
        job = AsyncJob(
            job_id=str(uuid.uuid4()),
            user_id=user_id,
            kind=kind,
            status=JobStatus.QUEUED,
            idempotency_key=idempotency_key,
            payload=payload or {},
            max_attempts=max_attempts,
            created_at=now,
            updated_at=now,
        )
        self._jobs[job.job_id] = job
        return job

    async def get(self, user_id: str, job_id: str) -> AsyncJob | None:
        job = self._jobs.get(job_id)
        if job is None or job.user_id != user_id:
            return None
        return job

    async def claim_next(self) -> AsyncJob | None:
        queued = sorted(
            (j for j in self._jobs.values() if j.status is JobStatus.QUEUED),
            key=lambda j: j.created_at,
        )
        if not queued:
            return None
        job = queued[0]
        updated = job.model_copy(
            update={
                "status": JobStatus.RUNNING,
                "attempt": job.attempt + 1,
                "updated_at": _now(),
            }
        )
        self._jobs[job.job_id] = updated
        return updated

    async def heartbeat(self, job_id: str) -> None:
        job = self._jobs.get(job_id)
        if job is None:
            return
        self._jobs[job_id] = job.model_copy(update={"updated_at": _now()})

    async def complete(self, job_id: str, result: dict[str, Any]) -> None:
        job = self._jobs[job_id]
        self._jobs[job_id] = job.model_copy(
            update={
                "status": JobStatus.SUCCEEDED,
                "result": result,
                "error": None,
                "updated_at": _now(),
            }
        )

    async def fail(self, job_id: str, error: str, *, retryable: bool = True) -> AsyncJob:
        job = self._jobs[job_id]
        if retryable and job.attempt < job.max_attempts:
            status = JobStatus.QUEUED
        elif retryable:
            status = JobStatus.DEAD_LETTER
        else:
            status = JobStatus.FAILED
        updated = job.model_copy(
            update={"status": status, "error": error, "updated_at": _now()}
        )
        self._jobs[job_id] = updated
        return updated
