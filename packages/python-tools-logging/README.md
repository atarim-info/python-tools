# python-tools-logging

structlog-based structured logging with PII masking and correlation/trace IDs.

## Install

```bash
uv add python-tools-logging
```

## Usage

```python
from python_tools.config import BaseServiceSettings
from python_tools.logging import bind_correlation_id, configure_logging, get_logger

settings = BaseServiceSettings(service_name="cv-service")
configure_logging(settings)

bind_correlation_id("req-123")
log = get_logger(__name__)
log.info("processing", user_email="dana@example.com")
# -> email is masked; correlation_id + trace IDs attached automatically
```

## What gets masked

| Type | Example in | Logged as |
|---|---|---|
| Email | `dana@example.com` | `***@example.com` |
| Phone | `+972 50-123-4567` | `***` |
| National ID | `123456789` | `***` |
| Free-text body | keys like `cv_body`, `document`, `text` | `<redacted len=N>` |

Masking runs as a structlog processor, so it applies to every event regardless of
call site. Test vectors include Hebrew text.

## Context

`bind_correlation_id`, `bind_request_id`, `get_correlation_id`, `get_request_id`,
and `clear_context` manage per-context IDs. If OpenTelemetry is installed and a span
is active, `trace_id` / `span_id` are attached automatically.
