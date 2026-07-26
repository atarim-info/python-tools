"""Authentication principals and standalone API-key auth (PT-06 Wave 1).

JWT / JWKS verification (T6.1-T6.3) lands when a consumer pulls Wave 3.
"""

from __future__ import annotations

from python_tools.auth.api_key import ApiKeyAuth, StandaloneAuth, parse_api_key_map
from python_tools.auth.errors import AuthError, ForbiddenError
from python_tools.auth.principal import Principal

__all__ = [
    "ApiKeyAuth",
    "AuthError",
    "ForbiddenError",
    "Principal",
    "StandaloneAuth",
    "parse_api_key_map",
]

__version__ = "0.1.0"
