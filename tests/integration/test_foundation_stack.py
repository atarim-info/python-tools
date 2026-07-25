"""Integration tests: the three P1 packages cooperate in one process."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from pydantic import SecretStr
from python_tools.config import BaseServiceSettings, Environment
from python_tools.logging import (
    bind_correlation_id,
    clear_context,
    configure_logging,
    get_logger,
)
from python_tools.obs import HealthRegistry, setup_observability

pytestmark = pytest.mark.integration

REPO_ROOT = Path(__file__).resolve().parents[2]


class _Settings(BaseServiceSettings):
    api_key: SecretStr | None = None


def test_secret_and_pii_never_reach_logs(capsys) -> None:
    clear_context()
    settings = _Settings(
        service_name="stack-svc",
        environment=Environment.PROD,
        api_key=SecretStr("super-secret"),
    )
    configure_logging(settings, json_logs=True)
    setup_observability(settings)
    bind_correlation_id("corr-stack")

    log = get_logger("integration")
    log.info("starting", config=settings.redacted_dump())
    log.info("request", user_email="dana@example.com", national_id="123456789")

    out = capsys.readouterr().out
    assert "super-secret" not in out
    assert "dana@example.com" not in out
    assert "123456789" not in out

    records = [json.loads(line) for line in out.strip().splitlines() if line.strip()]
    assert any(r.get("correlation_id") == "corr-stack" for r in records)
    clear_context()


def test_readiness_reflects_dependency_health() -> None:
    reg = HealthRegistry()
    reg.register("db", lambda: True)
    reg.register("kafka", lambda: False)
    report = reg.readiness()
    assert report.ready is False
    names = {c.name for c in report.checks}
    assert names == {"db", "kafka"}


def test_example_script_runs_as_subprocess() -> None:
    script = REPO_ROOT / "examples" / "hello_settings.py"
    result = subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stderr
    combined = result.stdout + result.stderr
    assert "do-not-log-me" not in combined
    assert "dana@example.com" not in combined
