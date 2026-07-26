"""Unit tests for standalone API-key auth (T6.4)."""

from __future__ import annotations

import pytest
from python_tools.auth import ApiKeyAuth, AuthError, Principal, parse_api_key_map


def test_parse_api_key_map() -> None:
    assert parse_api_key_map("a:u1, b:u2") == {"a": "u1", "b": "u2"}
    assert parse_api_key_map("") == {}
    assert parse_api_key_map("nope") == {}


def test_authenticate_success() -> None:
    auth = ApiKeyAuth({"k": "user-1"}, admin_user_ids=frozenset({"user-1"}))
    principal = auth.authenticate("k")
    assert principal == Principal(user_id="user-1", is_admin=True)


def test_authenticate_missing_and_invalid() -> None:
    auth = ApiKeyAuth.from_env_string("k:user-1")
    with pytest.raises(AuthError, match="missing"):
        auth.authenticate(None)
    with pytest.raises(AuthError, match="invalid"):
        auth.authenticate("wrong")
