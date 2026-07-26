"""Unit tests for python_tools.storage (PT-11 Wave 1)."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest
from python_tools.storage import (
    InMemoryDatabase,
    UnsafeKeyError,
    ensure_bucket,
    ensure_indexes,
    put_bytes,
    safe_key,
)


def test_safe_key_rejects_traversal() -> None:
    assert safe_key("a", "b", "c.txt") == "a/b/c.txt"
    assert safe_key("users/u1", "file.pdf", prefix="bin") == "bin/users/u1/file.pdf"
    with pytest.raises(UnsafeKeyError):
        safe_key("..", "etc", "passwd")
    with pytest.raises(UnsafeKeyError):
        safe_key("/abs")
    with pytest.raises(UnsafeKeyError):
        safe_key("a\\b")


def test_ensure_bucket_noop_and_create() -> None:
    from botocore.exceptions import ClientError

    ensure_bucket(None, "x")
    client = MagicMock()
    client.head_bucket.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": "n"}}, "HeadBucket"
    )
    ensure_bucket(client, "bucket")
    client.create_bucket.assert_called_once_with(Bucket="bucket")


def test_put_bytes_sets_sse(monkeypatch: pytest.MonkeyPatch) -> None:
    client = MagicMock()
    key = put_bytes(client, bucket="b", key="a/b.bin", data=b"hi")
    assert key == "a/b.bin"
    kwargs = client.put_object.call_args.kwargs
    assert kwargs["ServerSideEncryption"] == "AES256"
    assert kwargs["Body"] == b"hi"


@pytest.mark.asyncio
async def test_ensure_indexes_idempotent_on_memory() -> None:
    db = InMemoryDatabase()
    specs: list[tuple[str, list[tuple[str, int]], dict[str, Any]]] = [
        ("async_jobs", [("status", 1), ("created_at", 1)], {"name": "status_created"}),
        ("async_jobs", [("user_id", 1), ("idempotency_key", 1)], {"unique": True, "name": "uq"}),
    ]
    await ensure_indexes(db, specs)
    await ensure_indexes(db, specs)
    assert len(db["async_jobs"].indexes) >= 2
