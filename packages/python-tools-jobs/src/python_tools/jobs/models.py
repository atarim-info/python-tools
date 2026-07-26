"""Async job model + HTTP ``202`` / poll contract (PT-10 T10.1)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class JobStatus(StrEnum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    DEAD_LETTER = "dead_letter"


class AsyncJob(BaseModel):
    """Canonical job document stored by :class:`~python_tools.jobs.protocol.JobStore`."""

    job_id: str
    user_id: str
    kind: str
    status: JobStatus = JobStatus.QUEUED
    idempotency_key: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] | None = None
    error: str | None = None
    progress: float | None = None
    attempt: int = 0
    max_attempts: int = 3
    created_at: str
    updated_at: str

    def to_status_response(self) -> dict[str, Any]:
        """Shape returned by ``GET /jobs/{id}`` (and echoed from ``202`` create)."""
        return {
            "job_id": self.job_id,
            "kind": self.kind,
            "status": self.status.value,
            "progress": self.progress,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


# HTTP contract notes (for consumers / OpenAPI):
# - POST that starts work → ``202 Accepted`` with ``Location: /jobs/{job_id}``
#   and body = ``to_status_response()``.
# - Client polls ``GET /jobs/{job_id}`` until status is terminal
#   (succeeded | failed | dead_letter).
JOB_HTTP_CONTRACT = """
POST → 202 Accepted
  Location: /jobs/{job_id}
  Body: {job_id, kind, status, progress, result, error, created_at, updated_at}

GET /jobs/{job_id} → 200
  Body: same status shape; poll until status ∈ {succeeded, failed, dead_letter}
"""
