"""Async jobs: model, stores, and worker loop (PT-10 Wave 1)."""

from __future__ import annotations

from python_tools.jobs.memory import InMemoryJobStore
from python_tools.jobs.models import JOB_HTTP_CONTRACT, AsyncJob, JobStatus
from python_tools.jobs.mongo import MongoJobStore
from python_tools.jobs.protocol import JobStore
from python_tools.jobs.worker import run_worker_loop

__all__ = [
    "JOB_HTTP_CONTRACT",
    "AsyncJob",
    "InMemoryJobStore",
    "JobStatus",
    "JobStore",
    "MongoJobStore",
    "run_worker_loop",
]

__version__ = "0.1.0"
