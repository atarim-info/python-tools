"""Base settings, environment enums, and file-secret loading."""

from __future__ import annotations

import os
from enum import Enum, StrEnum
from pathlib import Path
from typing import Any

from pydantic import SecretStr
from pydantic.fields import FieldInfo
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)

_REDACTED = "***"


class Environment(StrEnum):
    """Deployment environment."""

    DEV = "dev"
    STAGING = "staging"
    PROD = "prod"


class ServiceMode(StrEnum):
    """How the service is running.

    ``web`` serves HTTP, ``worker`` runs background jobs, ``cli`` is a one-shot tool.
    """

    WEB = "web"
    WORKER = "worker"
    CLI = "cli"


class FileSecretSource(PydanticBaseSettingsSource):
    """Load field values from files referenced by ``<ENV_PREFIX><FIELD>_FILE`` env vars.

    Supports Vault-injected file secrets (INF-31): the orchestrator writes the secret
    to a file on disk and exposes only the *path* through an environment variable, so
    the plaintext never appears in the process environment.
    """

    def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        prefix = str(self.config.get("env_prefix", ""))
        env_name = f"{prefix}{field_name}_FILE".upper()
        path = os.environ.get(env_name)
        if path is None:
            return None, field_name, False
        value = Path(path).read_text(encoding="utf-8").strip()
        return value, field_name, False

    def prepare_field_value(
        self, field_name: str, field: FieldInfo, value: Any, value_is_complex: bool
    ) -> Any:
        return value

    def __call__(self) -> dict[str, Any]:
        data: dict[str, Any] = {}
        for field_name, field in self.settings_cls.model_fields.items():
            value, key, _ = self.get_field_value(field, field_name)
            if value is not None:
                data[key] = value
        return data


class BaseServiceSettings(BaseSettings):
    """Base class every python-tools service settings object inherits from.

    Reads, in order of precedence: explicit init kwargs, environment variables
    (``PT_`` prefix, ``__`` nesting), file secrets (``PT_<FIELD>_FILE``), then any
    ``.env`` file. Subclasses add their own fields.
    """

    model_config = SettingsConfigDict(
        env_prefix="PT_",
        env_nested_delimiter="__",
        case_sensitive=False,
        extra="ignore",
    )

    service_name: str
    environment: Environment = Environment.DEV
    log_level: str = "INFO"
    mode: ServiceMode = ServiceMode.WEB

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            FileSecretSource(settings_cls),
            dotenv_settings,
            file_secret_settings,
        )

    def redacted_dump(self) -> dict[str, Any]:
        """Return a dict of settings safe to log: secrets replaced with ``"***"``.

        Suitable for emitting at startup. Enum values are rendered as their string
        value; :class:`~pydantic.SecretStr` fields never expose their contents.
        """

        result: dict[str, Any] = {}
        for name in type(self).model_fields:
            value = getattr(self, name)
            if isinstance(value, SecretStr):
                result[name] = _REDACTED
            elif isinstance(value, Enum):
                result[name] = value.value
            else:
                result[name] = value
        return result
