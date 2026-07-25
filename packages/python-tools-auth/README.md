# python-tools-auth (stub)

Reserved distribution — implemented in **Phase P2**. Import root `python_tools.auth`.

Planned responsibility (PT-06): UTMS JWT verification (RS256 + JWKS cache/rotation),
`app_scope` enforcement, permission-check client (Redis, TTL ≤ 60s, fail-closed),
API-key principals for standalone mode, and FastAPI auth dependencies.

Depends on: `python-tools-config`, `python-tools-logging`.
