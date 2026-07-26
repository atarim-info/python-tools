"""Standalone API-key authentication (PT-06 T6.4).

Maps a static API key to a trusted ``user_id``. Intended for JFP standalone
mode and local/dev until UTMS JWKS lands (T6.1).
"""

from __future__ import annotations

from python_tools.auth.errors import AuthError
from python_tools.auth.principal import Principal


def parse_api_key_map(raw: str) -> dict[str, str]:
    """Parse ``api_key:user_id`` pairs separated by commas into a dict."""
    result: dict[str, str] = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if not pair or ":" not in pair:
            continue
        key, user_id = pair.split(":", 1)
        key, user_id = key.strip(), user_id.strip()
        if key and user_id:
            result[key] = user_id
    return result


class ApiKeyAuth:
    """Authenticate a bearer/API key against a static map.

    Downstream interface matches the future JWT verifier: ``authenticate`` →
    :class:`Principal` or :class:`AuthError`.
    """

    def __init__(self, key_map: dict[str, str], *, admin_user_ids: frozenset[str] | None = None):
        self._keys = dict(key_map)
        self._admins = admin_user_ids or frozenset()

    @classmethod
    def from_env_string(
        cls,
        raw: str,
        *,
        admin_user_ids: frozenset[str] | None = None,
    ) -> ApiKeyAuth:
        return cls(parse_api_key_map(raw), admin_user_ids=admin_user_ids)

    def authenticate(self, api_key: str | None) -> Principal:
        if not api_key:
            raise AuthError("missing API key")
        user_id = self._keys.get(api_key)
        if not user_id:
            raise AuthError("invalid API key")
        return Principal(user_id=user_id, is_admin=user_id in self._admins)


# Alias matching the cv-service shim name.
StandaloneAuth = ApiKeyAuth
