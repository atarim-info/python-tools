"""``Idempotency-Key`` extraction helper (PT-07 T7.3)."""

from __future__ import annotations

from typing import Any


def extract_idempotency_key(headers: Any, *, header_name: str = "Idempotency-Key") -> str | None:
    """Return the idempotency key from a mapping / Starlette Headers, or None."""
    value = headers.get(header_name) if headers is not None else None
    if value is None and headers is not None and hasattr(headers, "items"):
        for key, val in headers.items():
            if str(key).lower() == header_name.lower():
                value = val
                break
    if value is None:
        return None
    text = str(value).strip()
    return text or None
