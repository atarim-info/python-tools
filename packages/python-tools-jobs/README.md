# python-tools-jobs (stub)

Reserved distribution — implemented in **Phase P2**. Import root `python_tools.jobs`.

Planned responsibility (PT-10): job model + `202`/polling contract, Mongo & Postgres
store implementations behind one protocol, idempotent submission, and a worker loop
with claim, heartbeat, retry/backoff, and dead-letter marking.

Depends on: `python-tools-logging`.
