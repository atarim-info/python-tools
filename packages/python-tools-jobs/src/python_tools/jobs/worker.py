"""Worker claim loop with heartbeat / retry / dead-letter (PT-10 T10.3)."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from python_tools.jobs.models import AsyncJob
from python_tools.jobs.protocol import JobStore
from python_tools.logging import get_logger

JobHandler = Callable[[AsyncJob], Awaitable[dict[str, Any] | None]]

DEFAULT_POLL_INTERVAL_SECONDS = 1.0
DEFAULT_HEARTBEAT_SECONDS = 15.0


async def _heartbeat_loop(
    store: JobStore,
    job_id: str,
    stop: asyncio.Event,
    heartbeat_interval: float,
) -> None:
    while not stop.is_set():
        try:
            await asyncio.wait_for(stop.wait(), timeout=heartbeat_interval)
        except TimeoutError:
            await store.heartbeat(job_id)


async def run_worker_loop(
    store: JobStore,
    handler: JobHandler,
    *,
    poll_interval: float = DEFAULT_POLL_INTERVAL_SECONDS,
    heartbeat_interval: float = DEFAULT_HEARTBEAT_SECONDS,
    stop_after_idle: bool = False,
    max_jobs: int | None = None,
) -> int:
    """Poll ``store.claim_next`` and dispatch to ``handler``.

    Returns the number of jobs processed. On handler failure the job is failed
    with ``retryable=True`` (re-queue until ``max_attempts``, then dead-letter).
    """
    log = get_logger("jobs.worker")
    log.info("worker_started")
    processed = 0
    while True:
        job = await store.claim_next()
        if job is None:
            if stop_after_idle or (max_jobs is not None and processed >= max_jobs):
                return processed
            await asyncio.sleep(poll_interval)
            continue

        stop_heartbeat = asyncio.Event()
        hb_task = asyncio.create_task(
            _heartbeat_loop(store, job.job_id, stop_heartbeat, heartbeat_interval)
        )
        try:
            result = await handler(job)
            await store.complete(job.job_id, result or {})
            log.info("job_succeeded", job_id=job.job_id, kind=job.kind)
        except Exception as exc:
            updated = await store.fail(job.job_id, str(exc), retryable=True)
            log.error(
                "job_failed",
                job_id=job.job_id,
                kind=job.kind,
                error=str(exc),
                status=updated.status.value,
            )
        finally:
            stop_heartbeat.set()
            await hb_task

        processed += 1
        if max_jobs is not None and processed >= max_jobs:
            return processed
