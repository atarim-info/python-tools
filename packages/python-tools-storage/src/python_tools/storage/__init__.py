"""Storage helpers: S3/MinIO, Mongo indexes, in-memory DB (PT-11 Wave 1)."""

from __future__ import annotations

from python_tools.storage.indexes import IndexSpec, ensure_indexes
from python_tools.storage.keys import UnsafeKeyError, safe_key
from python_tools.storage.memory import InMemoryCollection, InMemoryDatabase
from python_tools.storage.mongo import create_mongo_database
from python_tools.storage.s3 import (
    create_s3_client,
    ensure_bucket,
    presign_get,
    presign_put,
    put_bytes,
)

__all__ = [
    "InMemoryCollection",
    "InMemoryDatabase",
    "IndexSpec",
    "UnsafeKeyError",
    "create_mongo_database",
    "create_s3_client",
    "ensure_bucket",
    "ensure_indexes",
    "presign_get",
    "presign_put",
    "put_bytes",
    "safe_key",
]

__version__ = "0.1.0"
