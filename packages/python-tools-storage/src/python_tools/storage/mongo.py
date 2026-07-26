"""Mongo client helper (PT-11 companion to indexes)."""

from __future__ import annotations

from typing import Any


def create_mongo_database(
    uri: str,
    database: str,
    *,
    uuid_representation: str = "standard",
) -> Any:
    """Return a Motor database handle for ``uri`` / ``database``."""
    try:
        from motor.motor_asyncio import AsyncIOMotorClient  # type: ignore[import-not-found]
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError(
            "motor is required for create_mongo_database. "
            "Install python-tools-storage[mongo]."
        ) from exc

    client = AsyncIOMotorClient(uri, uuidRepresentation=uuid_representation)
    return client[database]
