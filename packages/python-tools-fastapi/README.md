# python-tools-fastapi (stub)

Reserved distribution — implemented in **Phase P2**. Import root `python_tools.web`
(the distribution is named `python-tools-fastapi`).

Planned responsibility (PT-07): app factory (wires logging + observability), standard
error envelope + shared error-code enum, request-ID / access-log / exception-mapping
middleware, and helpers for cursor pagination, ETag/`If-Match`, and `Idempotency-Key`.

Depends on: `python-tools-observability`, `python-tools-auth`.
