"""OpenTelemetry bootstrap.

No-op by default: a tracer/meter provider is installed with the correct resource
attributes but no exporter, so tests and CLIs incur no external I/O. Pass
``enabled=True`` (and install the ``otlp`` extra) to export over OTLP.
"""

from __future__ import annotations

import importlib.metadata
from dataclasses import dataclass
from typing import Any

from opentelemetry import metrics, trace
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from python_tools.config import BaseServiceSettings


def _service_version(package: str = "python-tools-observability") -> str:
    try:
        return importlib.metadata.version(package)
    except importlib.metadata.PackageNotFoundError:
        return "0.0.0"


@dataclass
class Observability:
    """Handle to the configured providers. Kept small on purpose."""

    tracer_provider: TracerProvider
    meter_provider: MeterProvider
    enabled: bool

    def get_tracer(self, name: str) -> trace.Tracer:
        return self.tracer_provider.get_tracer(name)

    def get_meter(self, name: str) -> metrics.Meter:
        return self.meter_provider.get_meter(name)


def setup_observability(
    settings: BaseServiceSettings,
    *,
    enabled: bool = False,
    otlp_endpoint: str | None = None,
    resource_attributes: dict[str, Any] | None = None,
) -> Observability:
    """Install OTel tracer/meter providers with standard resource attributes.

    When ``enabled`` is False (the default) no exporter is attached — spans and metrics
    are created but go nowhere, which is what tests and CLI tools want.
    """

    resource = Resource.create(
        {
            "service.name": settings.service_name,
            "service.version": _service_version(),
            "deployment.environment": settings.environment.value,
            **(resource_attributes or {}),
        }
    )

    tracer_provider = TracerProvider(resource=resource)
    if enabled:
        _attach_otlp_exporter(tracer_provider, otlp_endpoint)
    trace.set_tracer_provider(tracer_provider)

    meter_provider = MeterProvider(resource=resource)
    metrics.set_meter_provider(meter_provider)

    return Observability(tracer_provider, meter_provider, enabled)


def _attach_otlp_exporter(tracer_provider: TracerProvider, endpoint: str | None) -> None:
    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (  # type: ignore[import-not-found]
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError as exc:  # pragma: no cover - exercised only with otlp extra
        raise RuntimeError(
            "OTLP export requested but the 'otlp' extra is not installed. "
            "Install python-tools-observability[otlp]."
        ) from exc

    exporter = OTLPSpanExporter(endpoint=endpoint) if endpoint else OTLPSpanExporter()
    tracer_provider.add_span_processor(BatchSpanProcessor(exporter))
