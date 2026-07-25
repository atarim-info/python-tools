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

Reserved as stubs (later phases): `auth`, `fastapi`, `events`, `jobs`, `storage`,
`llm`, `testing`.

The legacy `utils/` scripts are unrelated and kept untouched for now.

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
