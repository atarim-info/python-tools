"""Path-traversal-safe object key builder (PT-11 T11.1)."""

from __future__ import annotations


class UnsafeKeyError(ValueError):
    """Raised when a key segment would escape the intended prefix."""


def safe_key(*parts: str, prefix: str = "") -> str:
    """Join key parts, rejecting ``..``, absolute paths, and backslashes."""
    cleaned: list[str] = []
    if prefix:
        cleaned.append(prefix.strip("/"))
    for part in parts:
        raw = str(part).strip()
        if not raw:
            continue
        if "\\" in raw or raw.startswith("/") or raw.startswith("~"):
            raise UnsafeKeyError(f"unsafe key segment: {part!r}")
        text = raw.strip("/")
        if not text:
            raise UnsafeKeyError(f"unsafe key segment: {part!r}")
        for segment in text.split("/"):
            if segment in ("", ".", ".."):
                raise UnsafeKeyError(f"unsafe key segment: {part!r}")
            cleaned.append(segment)
    if not cleaned:
        raise UnsafeKeyError("empty object key")
    return "/".join(cleaned)
