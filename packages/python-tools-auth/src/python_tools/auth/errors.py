"""Auth failures. Consumers map these to HTTP 401/403."""

from __future__ import annotations


class AuthError(Exception):
    """Raised when a credential is missing or invalid."""


class ForbiddenError(Exception):
    """Raised when a principal is authenticated but not authorized."""
