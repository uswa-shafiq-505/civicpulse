# Scratch notes

## Day 1
- No blocking failure. Seed confirmed idempotent (`1.2_seed-idempotent.png`); network isolation confirmed failing as intended (`1.5_network-isolation-backend.png`).

# Day 2
- Broke: pasted bash `&&` chains into PowerShell; "token '&&' is not a valid statement separator."
- Believed: Node was not installed (winget said it was already present).
- Actual cause: Node existed at `C:\Program Files\nodejs` but was not on the User PATH.
- Fixed: added it via `[Environment]::SetEnvironmentVariable`, reopened terminal. Also used `--legacy-peer-deps` for `openapi-typescript@7` vs TypeScript 6 in the frontend.

# Day 3 acceptance results
1 pass - client-side validation, no network call
2 pass - valid submit -> category/priority/AI summary/llm:groq
3 pass - broken key -> rules:fallback (screenshot 3.5, providers 3.6)
4 pass - dashboard filters + pagination + page reset
5 pass - dashboard shows verbatim 409 message
6 pass (terminal) - 429 + Retry-After confirmed via burst loop
6 pending (UI) - UI 429 alert screenshot not captured; backend limiter confirmed working

## Day 4
- Broke: `StatsPage` test failed with `Unable to find an element by: [data-testid="cache-badge"]` — the test and the component disagreed on the testid.
- Believed: the component was wrong.
- Actual: the component rendered `cache-status` and the test was looking for `cache-badge`. Fixed by aligning the test to the component's `cache-status`.
- Note: local `npm test` now shows `Tests 8 passed (8)`; the `Error: kaboom` lines in the output are expected (ErrorBoundary test deliberately throws).

# Day 5 scratch

- Broke: `docker compose up` failed with `sqlalchemy.exc.ProgrammingError: type "category_enum" already exists` on a fresh volume.
- Believed first: volume was not wiped by `docker compose down -v`. Removed it explicitly with `docker volume rm civicpulse_pgdata` — still failed.
- Believed second: `db-init` racing the backend on schema creation. Ruled out after grepping `backend/app/` for `create_all` (none) and checking the backend `CMD` (only uvicorn, no `alembic upgrade`).
- Actual cause: in `backend/alembic/versions/0001_initial_schema.py`, the migration defines `postgresql.ENUM` values AND calls `.create(bind, checkfirst=True)` explicitly, AND then uses them inside `op.create_table`. `postgresql.ENUM` auto-issues `CREATE TYPE` during `create_table` unless `create_type=False`. So the type was created once explicitly and once implicitly — the second attempt failed.
- Fixed: added `create_type=False` to the three enum definitions at the top of the migration. Explicit `.create(bind, checkfirst=True)` calls remain the single owner of creation.
- Also discovered on Day 5: the backend image has neither `ping` nor `wget`, so isolation checks must use Python — `socket.gethostbyname('postgres')` and `urllib.request.urlopen(...)`.
- Also discovered: `db-init` needs both `working_dir: /app` and `PYTHONPATH: /app`, or `alembic` cannot import `app.config` and fails with `ModuleNotFoundError: No module named 'app'`.

## Redis volume justification (§2.4)

Redis does two jobs in CivicPulse. The stats cache could be rebuilt from Postgres
freely — losing it costs one extra database query. But the rate-limit counters
and the 24 h LLM triage cache hold real cost: the limiter is the only thing
standing between one bored user and our entire daily Groq quota, and the triage
cache saves inference for duplicate complaints (a burst main gets reported by
nine neighbours). If Redis restarted empty, a caller could reset their own rate
limit and re-spend inference quota. Persisting AOF is therefore cheap insurance
against a class of abuse and cost, not a way to preserve reproducible state.