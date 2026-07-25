# python-tools-observability

OpenTelemetry bootstrap, a pluggable health-check registry, and Prometheus metrics.

## Install

```bash
uv add python-tools-observability          # no-op tracing (tests/CLI)
uv add "python-tools-observability[otlp]"  # + OTLP gRPC exporter
```

## Usage

```python
from python_tools.config import BaseServiceSettings
from python_tools.obs import HealthRegistry, setup_observability

settings = BaseServiceSettings(service_name="cv-service")
obs = setup_observability(settings)  # no-op by default
tracer = obs.get_tracer(__name__)

health = HealthRegistry()
health.register("db", lambda: True)
print(health.readiness().as_dict())
```

## Behaviour

- `setup_observability(settings)` installs tracer/meter providers with
  `service.name` / `service.version` / `deployment.environment` resource attributes.
- No exporter is attached unless `enabled=True` (requires the `otlp` extra) — so tests
  and CLI usage are zero-config and do no network I/O.
- `HealthRegistry.readiness()` runs all registered checks and **fails closed** if any
  check returns False or raises.
- `render_metrics()` returns Prometheus text; the web package serves it at `/metrics`.
