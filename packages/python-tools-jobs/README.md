# python-tools-jobs

Import root: `python_tools.jobs`.

## Wave 1

Job model + `202`/poll contract, in-memory + Mongo stores, idempotent
submission, and a worker claim loop with heartbeat / retry / dead-letter.

```python
from python_tools.jobs import InMemoryJobStore, run_worker_loop

store = InMemoryJobStore()
job = await store.create("user-1", "import_cv", idempotency_key="k1")

async def handle(job):
    return {"ok": True}

await run_worker_loop(store, handle, stop_after_idle=True, max_jobs=1)
```

Install Mongo support with `python-tools-jobs[mongo]` (`motor`).

Postgres store (T10.2b) is deferred until a consumer asks.

Depends on: `python-tools-config`, `python-tools-logging`.
