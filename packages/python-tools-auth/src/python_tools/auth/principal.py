"""Downstream principal shape shared by API-key and (later) JWT paths."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Principal:
    """Authenticated actor exposed to route handlers and job workers.

    Wave 1 (standalone) fills ``user_id`` (+ optional ``is_admin``). JWT path
    (Wave 3) will populate ``permissions``, ``app_scope``, and ``acting_as``
    without changing this interface.
    """

    user_id: str
    is_admin: bool = False
    permissions: frozenset[str] = field(default_factory=frozenset)
    app_scope: str | None = None
    acting_as: str | None = None
