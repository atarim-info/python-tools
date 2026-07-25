"""Shared service configuration for python-tools consumers.

Provides :class:`BaseServiceSettings` — a ``pydantic-settings`` base class with the
platform's env-var conventions, Vault-injected file-secret loading (INF-31), and a
``redacted_dump()`` that never emits secret values.
"""

from __future__ import annotations

from python_tools.config.settings import (
    BaseServiceSettings,
    Environment,
    FileSecretSource,
    ServiceMode,
)

__all__ = [
    "BaseServiceSettings",
    "Environment",
    "FileSecretSource",
    "ServiceMode",
]

__version__ = "0.1.0"
