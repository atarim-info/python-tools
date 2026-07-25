# python-tools-config

`pydantic-settings` base class with the platform's environment conventions,
Vault-injected file-secret loading (INF-31), and redacted config dumps.

## Install

```bash
uv add python-tools-config
```

## Usage

```python
from pydantic import SecretStr
from python_tools.config import BaseServiceSettings, Environment


class Settings(BaseServiceSettings):
    api_key: SecretStr | None = None
    max_workers: int = 4


settings = Settings(service_name="cv-service", environment=Environment.PROD)
print(settings.redacted_dump())  # api_key -> "***"
```

## Conventions

| Concern | Behaviour |
|---|---|
| Env prefix | `PT_` (e.g. `PT_SERVICE_NAME`) |
| Nested delimiter | `__` (e.g. `PT_DB__HOST`) |
| File secrets | `PT_<FIELD>_FILE` points to a file whose contents is the value |
| Redaction | `redacted_dump()` replaces every `SecretStr` with `"***"` |

## Fields on `BaseServiceSettings`

- `service_name: str` (required)
- `environment: Environment` = `dev`
- `log_level: str` = `INFO`
- `mode: ServiceMode` = `web`
