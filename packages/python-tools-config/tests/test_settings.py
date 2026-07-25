from __future__ import annotations

from pathlib import Path

from pydantic import SecretStr
from python_tools.config import BaseServiceSettings, Environment, ServiceMode


class Settings(BaseServiceSettings):
    api_key: SecretStr | None = None
    max_workers: int = 4


def test_defaults() -> None:
    s = Settings(service_name="svc")
    assert s.service_name == "svc"
    assert s.environment is Environment.DEV
    assert s.mode is ServiceMode.WEB
    assert s.log_level == "INFO"


def test_env_overrides(monkeypatch) -> None:
    monkeypatch.setenv("PT_SERVICE_NAME", "cv-service")
    monkeypatch.setenv("PT_ENVIRONMENT", "prod")
    monkeypatch.setenv("PT_MAX_WORKERS", "16")
    s = Settings()
    assert s.service_name == "cv-service"
    assert s.environment is Environment.PROD
    assert s.max_workers == 16


def test_file_secret_loading(monkeypatch, tmp_path: Path) -> None:
    secret_file = tmp_path / "api_key"
    secret_file.write_text("s3cr3t-value\n", encoding="utf-8")
    monkeypatch.setenv("PT_API_KEY_FILE", str(secret_file))
    s = Settings(service_name="svc")
    assert s.api_key is not None
    assert s.api_key.get_secret_value() == "s3cr3t-value"


def test_redacted_dump_hides_secrets() -> None:
    s = Settings(service_name="svc", api_key=SecretStr("top-secret"))
    dump = s.redacted_dump()
    assert dump["api_key"] == "***"
    assert dump["environment"] == "dev"
    assert dump["service_name"] == "svc"
    assert "top-secret" not in str(dump)


def test_redacted_dump_none_secret_stays_none() -> None:
    s = Settings(service_name="svc")
    assert s.redacted_dump()["api_key"] is None
