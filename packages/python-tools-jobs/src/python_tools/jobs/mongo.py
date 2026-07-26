"""Mongo-backed job store (PT-10 T10.2a)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from python_tools.jobs.models import AsyncJob, JobStatus


def _now() -> str:
    return datetime.now(UTC).isoformat()


class MongoJobStore:
    """Job store over a Motor/pymongo-like collection (``async_jobs`` by default)."""

    def __init__(self, db: Any, *, collection: str = "async_jobs") -> None:
        self._c = db[collection]

    def _from_doc(self, doc: dict[str, Any]) -> AsyncJob:
        return AsyncJob.model_validate(doc)

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
            existing = await self._c.find_one(
                {"user_id": user_id, "idempotency_key": idempotency_key}
            )
            if existing:
                return self._from_doc(existing)
        now = _now()
        doc: dict[str, Any] = {
            "job_id": str(uuid.uuid4()),
            "user_id": user_id,
            "kind": kind,
            "status": JobStatus.QUEUED.value,
            "idempotency_key": idempotency_key,
            "payload": payload or {},
            "result": None,
            "error": None,
            "progress": None,
            "attempt": 0,
            "max_attempts": max_attempts,
            "created_at": now,
            "updated_at": now,
        }
        await self._c.insert_one(doc)
        return self._from_doc(doc)

    async def get(self, user_id: str, job_id: str) -> AsyncJob | None:
        doc = await self._c.find_one({"user_id": user_id, "job_id": job_id})
        return self._from_doc(doc) if doc else None

    async def claim_next(self) -> AsyncJob | None:
        """Atomically claim the oldest queued job when the driver supports it."""
        now = _now()
        find_one_and_update = getattr(self._c, "find_one_and_update", None)
        if find_one_and_update is not None:
            try:
                from pymongo import ReturnDocument
            except ImportError:  # pragma: no cover
                ReturnDocument = None  # type: ignore[assignment,misc]
            if ReturnDocument is not None:
                doc = await find_one_and_update(
                    {"status": JobStatus.QUEUED.value},
                    {
                        "$set": {"status": JobStatus.RUNNING.value, "updated_at": now},
                        "$inc": {"attempt": 1},
                    },
                    sort=[("created_at", 1)],
                    return_document=ReturnDocument.AFTER,
                )
                return self._from_doc(doc) if doc else None

        # Fallback for in-memory / minimal collections (cv-service shim parity).
        queued = await self._c.find({"status": JobStatus.QUEUED.value}).sort(
            "created_at", 1
        ).limit(1).to_list(1)
        if not queued:
            return None
        job = queued[0]
        await self._c.update_one(
            {"job_id": job["job_id"], "status": JobStatus.QUEUED.value},
            {
                "$set": {"status": JobStatus.RUNNING.value, "updated_at": now},
                "$inc": {"attempt": 1},
            },
        )
        job["status"] = JobStatus.RUNNING.value
        job["attempt"] = int(job.get("attempt", 0)) + 1
        job["updated_at"] = now
        return self._from_doc(job)

    async def heartbeat(self, job_id: str) -> None:
        await self._c.update_one(
            {"job_id": job_id},
            {"$set": {"updated_at": _now()}},
        )

    async def complete(self, job_id: str, result: dict[str, Any]) -> None:
        await self._c.update_one(
            {"job_id": job_id},
            {
                "$set": {
                    "status": JobStatus.SUCCEEDED.value,
                    "result": result,
                    "error": None,
                    "updated_at": _now(),
                }
            },
        )

    async def fail(self, job_id: str, error: str, *, retryable: bool = True) -> AsyncJob:
        doc = await self._c.find_one({"job_id": job_id})
        if doc is None:
            raise KeyError(job_id)
        attempt = int(doc.get("attempt", 0))
        max_attempts = int(doc.get("max_attempts", 3))
        if retryable and attempt < max_attempts:
            status = JobStatus.QUEUED.value
        elif retryable:
            status = JobStatus.DEAD_LETTER.value
        else:
            status = JobStatus.FAILED.value
        await self._c.update_one(
            {"job_id": job_id},
            {"$set": {"status": status, "error": error, "updated_at": _now()}},
        )
        doc["status"] = status
        doc["error"] = error
        return self._from_doc(doc)
