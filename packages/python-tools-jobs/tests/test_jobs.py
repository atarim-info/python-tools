"""Unit tests for python_tools.jobs (PT-10 Wave 1)."""

from __future__ import annotations

import pytest
from python_tools.jobs import (
    AsyncJob,
    InMemoryJobStore,
    JobStatus,
    MongoJobStore,
    run_worker_loop,
)


@pytest.mark.asyncio
async def test_idempotent_create_and_status_shape() -> None:
    store = InMemoryJobStore()
    a = await store.create("u1", "import", idempotency_key="k", payload={"x": 1})
    b = await store.create("u1", "import", idempotency_key="k", payload={"x": 2})
    assert a.job_id == b.job_id
    body = a.to_status_response()
    assert body["job_id"] == a.job_id
    assert body["status"] == "queued"
    assert "kind" in body


@pytest.mark.asyncio
async def test_claim_complete() -> None:
    store = InMemoryJobStore()
    await store.create("u1", "k")
    job = await store.claim_next()
    assert job is not None
    assert job.status is JobStatus.RUNNING
    assert job.attempt == 1
    await store.complete(job.job_id, {"done": True})
    got = await store.get("u1", job.job_id)
    assert got is not None
    assert got.status is JobStatus.SUCCEEDED
    assert got.result == {"done": True}


@pytest.mark.asyncio
async def test_fail_retries_then_dead_letter() -> None:
    store = InMemoryJobStore()
    created = await store.create("u1", "k", max_attempts=2)
    for _ in range(2):
        job = await store.claim_next()
        assert job is not None
        updated = await store.fail(job.job_id, "boom", retryable=True)
    assert updated.status is JobStatus.DEAD_LETTER
    # Exhausted — nothing left to claim.
    assert await store.claim_next() is None
    assert created.job_id == updated.job_id


@pytest.mark.asyncio
async def test_worker_loop_success() -> None:
    store = InMemoryJobStore()
    await store.create("u1", "echo")

    async def handler(job: AsyncJob) -> dict[str, object]:
        return {"kind": job.kind}

    n = await run_worker_loop(store, handler, stop_after_idle=True, max_jobs=1)
    assert n == 1
    # Idle second pass returns immediately.
    n2 = await run_worker_loop(store, handler, stop_after_idle=True)
    assert n2 == 0


class _FakeCollection:
    """Minimal async collection for MongoJobStore fallback path."""

    def __init__(self) -> None:
        self.docs: list[dict[str, object]] = []

    async def find_one(self, flt: dict[str, object]) -> dict[str, object] | None:
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in flt.items()):
                return dict(doc)
        return None

    async def insert_one(self, doc: dict[str, object]) -> None:
        self.docs.append(dict(doc))

    def find(self, flt: dict[str, object]) -> _Cursor:
        matched = [dict(d) for d in self.docs if all(d.get(k) == v for k, v in flt.items())]
        return _Cursor(matched)

    async def update_one(self, flt: dict[str, object], update: dict[str, object]) -> None:
        for doc in self.docs:
            if all(doc.get(k) == v for k, v in flt.items()):
                for op, fields in update.items():
                    if op == "$set":
                        doc.update(fields)  # type: ignore[arg-type]
                    if op == "$inc":
                        for key, delta in fields.items():  # type: ignore[attr-defined]
                            doc[key] = int(doc.get(key, 0)) + int(delta)  # type: ignore[arg-type]
                return


class _Cursor:
    def __init__(self, docs: list[dict[str, object]]) -> None:
        self._docs = docs

    def sort(self, *_a: object, **_k: object) -> _Cursor:
        return self

    def limit(self, n: int) -> _Cursor:
        self._docs = self._docs[:n]
        return self

    async def to_list(self, length: int | None = None) -> list[dict[str, object]]:
        return self._docs if length is None else self._docs[:length]


class _FakeDb:
    def __init__(self) -> None:
        self.col = _FakeCollection()

    def __getitem__(self, name: str) -> _FakeCollection:
        return self.col


@pytest.mark.asyncio
async def test_mongo_store_idempotent_and_claim() -> None:
    store = MongoJobStore(_FakeDb())
    a = await store.create("u1", "import", idempotency_key="ik")
    b = await store.create("u1", "import", idempotency_key="ik")
    assert a.job_id == b.job_id
    claimed = await store.claim_next()
    assert claimed is not None
    assert claimed.status is JobStatus.RUNNING
    await store.heartbeat(claimed.job_id)
    await store.complete(claimed.job_id, {"ok": True})
    got = await store.get("u1", claimed.job_id)
    assert got is not None
    assert got.status is JobStatus.SUCCEEDED
