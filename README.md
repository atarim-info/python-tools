# python-tools

The company's shared Python foundation: the cross-cutting concerns every Python
service would otherwise re-implement — config, logging, observability, auth, HTTP
conventions, events, jobs, storage, LLM access, and test fixtures.

> Infrastructure-shaped concerns only. No business/domain logic lives here.
> See the PRD: `Documentation/python_tools/prd_python_tools/prd_python_tools.md`.

## Status — Phase P1 (Foundation)

Living readiness (update on every epic/story/task status change):
`Documentation/python_tools/Readiness/python_tools_readiness.md`

Stories / tasks breakdown:
`Documentation/python_tools/prd_python_tools/python_tools_stories_tasks.md`

Implemented:

| Distribution | Import | Responsibility |
|---|---|---|
| `python-tools-config` | `python_tools.config` | `BaseServiceSettings`, env conventions, file-secret loading, redacted dumps |
| `python-tools-logging` | `python_tools.logging` | structlog JSON logging, PII masking, correlation + trace IDs |
| `python-tools-observability` | `python_tools.obs` | OTel bootstrap (no-op by default), health check registry |
| `python-tools-auth` | `python_tools.auth` | Standalone API-key principals (JWT/JWKS deferred) |
| `python-tools-fastapi` | `python_tools.web` | App factory, error envelope, middleware, ETag/health routes |
| `python-tools-jobs` | `python_tools.jobs` | Async job model, Mongo/memory stores, worker claim loop |
| `python-tools-storage` | `python_tools.storage` | S3/MinIO helpers, Mongo indexes, in-memory DB |

Still stubs (later waves): `events`, `llm`, `testing`.

The legacy `utils/` scripts are unrelated and kept untouched for now.

## Consuming from another repo (until CodeArtifact)

Path dependency (local monorepo / sibling checkout):

```toml
[tool.uv.sources]
python-tools-config = { path = "../python-tools/packages/python-tools-config", editable = true }
python-tools-logging = { path = "../python-tools/packages/python-tools-logging", editable = true }
python-tools-observability = { path = "../python-tools/packages/python-tools-observability", editable = true }
python-tools-auth = { path = "../python-tools/packages/python-tools-auth", editable = true }
python-tools-fastapi = { path = "../python-tools/packages/python-tools-fastapi", editable = true }
python-tools-jobs = { path = "../python-tools/packages/python-tools-jobs", editable = true }
python-tools-storage = { path = "../python-tools/packages/python-tools-storage", editable = true }
```

Or pin a git tag / commit once Wave 1 is tagged:

```toml
python-tools-auth = { git = "https://github.com/atarim-info/python-tools.git", subdirectory = "packages/python-tools-auth", rev = "<tag-or-sha>" }
```

## Layout

```
packages/            one directory per published distribution
examples/            runnable smoke examples
tests/integration/   cross-package integration tests
docs/                design docs + package docs (MkDocs later)
```

## Development

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12+.

```bash
uv sync                         # create the workspace venv, install all packages
uv run ruff check .             # lint
uv run ruff format --check .    # format check
uv run mypy --config-file mypy.ini packages   # type check
uv run pytest                   # unit + integration tests
uv run python examples/hello_settings.py      # foundation smoke example
```

## Conventions

- Import root `python_tools.*` (PEP 420 namespace packages); every package ships `py.typed`.
- SemVer per distribution; independent versions (no lockstep).
- A concern enters `python-tools` only when ≥2 services need it, or it encodes a
  platform rule that must not diverge (the "two-service rule").

## Publishing

Distribution to the private AWS CodeArtifact index (PT-03) is not wired yet —
blocked on open question PTQ-1. Until then, consume from a pinned git tag.
