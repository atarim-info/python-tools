# python-tools-auth

Import root: `python_tools.auth`.

## Wave 1 (standalone)

API-key principals for services that run without UTMS JWKS (e.g. JFP
`operating_mode=standalone`).

```python
from python_tools.auth import ApiKeyAuth, AuthError

auth = ApiKeyAuth.from_env_string("dev-key:user-1,admin-key:admin-1")
principal = auth.authenticate("dev-key")  # Principal(user_id="user-1")
```

## Deferred (Wave 3)

- RS256 JWT verification + JWKS cache/rotation
- `app_scope` + permission-check client (Redis, fail-closed)
- Cross-principal authz library tests

Depends on: `python-tools-config`, `python-tools-logging`.
