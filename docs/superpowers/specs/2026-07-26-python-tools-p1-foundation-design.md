# python-tools — P1 Foundation Scaffold (Design)

**Date:** 2026-07-26
**Source PRD:** `Documentation/python_tools/prd_python_tools/prd_python_tools.md`
**Scope:** PRD Phase **P1 — Foundation** (PT-01…PT-03 + `config`, `logging`, `observability`).

## Decisions (from brainstorming)

- **Depth:** Option **B** — full uv workspace, all 10 package directories reserved,
  only `config` / `logging` / `observability` implemented with real (minimal) behaviour.
  The other seven packages ship as importable stubs.
- **Legacy `utils/`:** left untouched (Option A). The new workspace lives beside it.
- **Approach:** Option 1 — minimal workspace + P1 packages; a CLI example
  (`examples/hello_settings.py`) proves the three packages together (no FastAPI yet).

## Repo layout

```
python-tools/
  utils/                          # legacy — untouched
  packages/
    python-tools-config/          # implemented (P1)
    python-tools-logging/         # implemented (P1)
    python-tools-observability/   # implemented (P1)
    python-tools-auth/            # stub
    python-tools-fastapi/         # stub
    python-tools-events/          # stub
    python-tools-jobs/            # stub
    python-tools-storage/         # stub
    python-tools-llm/             # stub
    python-tools-testing/         # stub
  examples/hello_settings.py      # CLI smoke: settings + logs + obs no-op
  tests/integration/              # cross-package integration tests
  docs/                           # design + package README stubs (MkDocs later)
  .github/workflows/ci.yml
  pyproject.toml                  # uv workspace root
  ruff.toml, mypy.ini, .pre-commit-config.yaml
  CODEOWNERS, README.md, .gitignore
```

## Namespace

- Import root `python_tools.*` via PEP 420 implicit namespace packages
  (no top-level `python_tools/__init__.py` in any distribution).
- Each distribution owns exactly one submodule: `python_tools.config`, `python_tools.logging`, etc.
- Every package ships `py.typed`.

## Tooling

- Python **3.12** floor (`requires-python = ">=3.12"`); managed via uv.
- Shared **Ruff** (lint + format) and **strict mypy**, configured once at the root.
- `.pre-commit-config.yaml` runs ruff + ruff-format + mypy.
- CI (`.github/workflows/ci.yml`): matrix Python 3.12 / 3.13 →
  `uv sync` → ruff check → ruff format --check → mypy → pytest (unit) → pytest (integration).
- Publishing to AWS CodeArtifact (PT-03) is left as documented TODO — blocked on open question PTQ-1.

## P1 package APIs

### `python_tools.config`
- `Environment` enum (`dev`/`staging`/`prod`), `ServiceMode` enum (`web`/`worker`/`cli`).
- `BaseServiceSettings(pydantic_settings.BaseSettings)`: `service_name`, `environment`,
  `log_level`, `mode`, plus env-var conventions (`PT_` prefix, nested `__` delimiter).
- Vault file-secret loading: `SecretStr` fields resolvable from a `*_FILE` path (INF-31).
- `redacted_dump()` → dict with every `SecretStr` replaced by `"***"`; safe for startup logs.

### `python_tools.logging`
- `configure_logging(settings)` → structlog JSON in prod, console renderer in dev.
- PII masking processor: email, phone, national ID, long free-text bodies → masked;
  test vectors include Hebrew text.
- Correlation/request-ID contextvars + OTel trace/span-ID injection processor.
- `get_logger(name)` returning a bound structlog logger.

### `python_tools.obs`
- `setup_observability(settings, *, enabled=...)` bootstraps OTel tracer/meter + OTLP export;
  **no-op mode** (in-memory / disabled) by default for tests and CLI.
- `HealthRegistry` with pluggable checks; `liveness()` and `readiness()` results
  for later `/healthz` + `/readyz` wiring.
- `instrument_metrics()` helper exposing a Prometheus registry (no server started here).

## Stub packages

Each stub ships `pyproject.toml`, `src/python_tools/<name>/__init__.py` with a module
docstring + `__all__ = []` + `__version__`, and `py.typed`. They import cleanly and
declare their intended dependency direction in the README, but contain no logic yet.

## Testing boundary (P1)

- **Unit tests** per implemented package (config/logging/obs), ≥80% coverage target.
- **Integration tests** in `tests/integration/`:
  - all three distributions install and cooperate in a clean env,
  - env + file-secret loading,
  - secrets/PII never appear in `redacted_dump()` or emitted logs,
  - correlation + trace IDs propagate into log records,
  - OTel uses in-memory exporters (no external collector),
  - `examples/hello_settings.py` runs successfully as a subprocess.
- Docker/testcontainer integration (Kafka/Mongo/MinIO/Postgres) deferred to later phases.

## Out of scope for P1

Real implementations of auth, fastapi, events, jobs, storage, llm, testing;
CodeArtifact publishing; MkDocs site; the `create-service` starter template.
