"""Declarative Mongo index helper applied idempotently at startup (PT-11 T11.2)."""

from __future__ import annotations

from typing import Any

# (collection, keys, options) — pymongo IndexModel-friendly.
IndexSpec = tuple[str, list[tuple[str, int]], dict[str, Any]]


async def ensure_indexes(db: Any, specs: list[IndexSpec]) -> None:
    """Create indexes from declarative specs. Safe to call on every startup."""
    try:
        from pymongo import IndexModel
    except ImportError:
        for coll, keys, opts in specs:
            await db[coll].create_index(keys, **opts)
        return

    grouped: dict[str, list[Any]] = {}
    for coll, keys, opts in specs:
        grouped.setdefault(coll, []).append(IndexModel(keys, **opts))

    for coll, models in grouped.items():
        create_indexes = getattr(db[coll], "create_indexes", None)
        if create_indexes is not None:
            await create_indexes(models)
        else:
            for model in models:
                # IndexModel.document includes key + options; prefer kwargs form.
                await db[coll].create_index(model.document["key"], **{
                    k: v for k, v in model.document.items() if k != "key"
                })
