# python-tools-llm (stub)

Reserved distribution — implemented in **Phase P3**. Import root `python_tools.llm`.

Planned responsibility (PT-12): provider port (direct vs gateway HTTP), model routing
returning `model_id`, a prompt/instruction pack loader with cascade
(`model_id` → family → provider → `default`), structured-output helper with
retry-on-parse-failure, and a stub provider for CI.

Depends on: `python-tools-config`, `python-tools-logging`.
