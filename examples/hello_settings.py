"""Foundation smoke example: config + logging + observability together.

Run it with:

    uv run python examples/hello_settings.py

It loads settings, configures structured logging (with PII masking), sets up
observability in no-op mode, emits a couple of log lines, and prints a readiness
report. Exit code 0 means the three P1 packages cooperate.
"""

from __future__ import annotations

from pydantic import SecretStr
from python_tools.config import BaseServiceSettings, Environment
from python_tools.logging import bind_correlation_id, configure_logging, get_logger
from python_tools.obs import HealthRegistry, setup_observability


class ExampleSettings(BaseServiceSettings):
    api_key: SecretStr | None = None


def main() -> None:
    settings = ExampleSettings(
        service_name="hello-service",
        environment=Environment.DEV,
        api_key=SecretStr("do-not-log-me"),
    )

    configure_logging(settings)
    obs = setup_observability(settings)

    bind_correlation_id("example-0001")
    log = get_logger("examples.hello_settings")

    log.info("service starting", config=settings.redacted_dump())
    log.info(
        "handling request",
        user_email="dana@example.com",
        phone="+972 50-123-4567",
    )

    tracer = obs.get_tracer("examples.hello_settings")
    with tracer.start_as_current_span("do-work"):
        log.info("did some work")

    health = HealthRegistry()
    health.register("self", lambda: True)
    log.info("readiness", report=health.readiness().as_dict())

    log.info("service stopping")


if __name__ == "__main__":
    main()
