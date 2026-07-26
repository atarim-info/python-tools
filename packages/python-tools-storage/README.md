# python-tools-storage

Import root: `python_tools.storage`.

## Wave 1

- S3/MinIO client helpers with SSE default, presign TTL, path-safe keys
- Mongo declarative index helper (`ensure_indexes`)
- In-memory document store for hermetic tests

```python
from python_tools.storage import safe_key, ensure_indexes, InMemoryDatabase

key = safe_key("users", user_id, "cv.pdf")  # rejects ".."
db = InMemoryDatabase()
await ensure_indexes(db, [("async_jobs", [("status", 1)], {"name": "status"})])
```

Extras: `python-tools-storage[mongo]`, `python-tools-storage[s3]`, or `[all]`.

Postgres / PgBouncer engine (T11.3) is deferred until a consumer asks.

Depends on: `python-tools-config`.
