"""ETag helpers + ``If-Match`` enforcement (PT-07 T7.3)."""

from __future__ import annotations


class EtagMismatch(Exception):
    """Raised when ``If-Match`` does not match the stored ETag → HTTP 412."""


def make_etag(revision: int) -> str:
    """Weak ETag from a monotonically increasing document revision."""
    return f'W/"{revision}"'


def check_if_match(current_etag: str, if_match: str | None) -> None:
    """Require ``If-Match`` to equal ``current_etag`` when the header is present."""
    if if_match is not None and current_etag != if_match:
        raise EtagMismatch("etag mismatch")
