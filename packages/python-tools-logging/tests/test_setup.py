from __future__ import annotations

import json

from python_tools.config import BaseServiceSettings, Environment
from python_tools.logging import (
    bind_correlation_id,
    clear_context,
    configure_logging,
    get_logger,
)


def test_json_logging_masks_and_adds_ids(capsys) -> None:
    clear_context()
    settings = BaseServiceSettings(service_name="svc", environment=Environment.PROD)
    configure_logging(settings, json_logs=True)
    bind_correlation_id("corr-42")

    get_logger("test").info("hello", user="dana@example.com")

    line = capsys.readouterr().out.strip().splitlines()[-1]
    record = json.loads(line)
    assert record["event"] == "hello"
    assert record["user"] == "***@example.com"
    assert record["correlation_id"] == "corr-42"
    assert record["level"] == "info"
    clear_context()


def test_dev_console_renderer_smoke(capsys) -> None:
    clear_context()
    settings = BaseServiceSettings(service_name="svc", environment=Environment.DEV)
    configure_logging(settings)
    get_logger("test").info("dev-mode")
    assert "dev-mode" in capsys.readouterr().out
