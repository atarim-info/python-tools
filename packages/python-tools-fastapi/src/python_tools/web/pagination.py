"""Cursor pagination helpers (PT-07 T7.3)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Page[T]:
    items: list[T]
    next_cursor: str | None
    has_more: bool


def paginate[T](items: list[T], *, limit: int, cursor: str | None = None) -> Page[T]:
    """Offset-style cursor: the cursor is the integer index as a decimal string."""
    start = int(cursor) if cursor else 0
    if start < 0:
        start = 0
    window = items[start : start + limit + 1]
    has_more = len(window) > limit
    page_items = window[:limit]
    next_cursor = str(start + limit) if has_more else None
    return Page(items=page_items, next_cursor=next_cursor, has_more=has_more)
