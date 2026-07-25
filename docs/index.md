# python-tools

Shared Python foundation for the platform. Infrastructure-shaped concerns only —
no business/domain logic.

## Phase P1 (implemented)

- [`python-tools-config`](../packages/python-tools-config/README.md) — settings, file secrets, redacted dumps
- [`python-tools-logging`](../packages/python-tools-logging/README.md) — structlog JSON + PII masking + trace IDs
- [`python-tools-observability`](../packages/python-tools-observability/README.md) — OTel bootstrap, health checks, metrics

## Reserved (later phases)

`auth`, `fastapi`, `events`, `jobs`, `storage`, `llm`, `testing` — importable stubs today.

## Design

See [P1 Foundation design](superpowers/specs/2026-07-26-python-tools-p1-foundation-design.md)
and the source PRD in the Documentation repo.

> A full MkDocs site is deferred (PT-14). This file is the docs seed.
