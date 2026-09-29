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

## Day 6
- Broke: CI failed with `ModuleNotFoundError: No module named 'app'` — `PYTHONPATH: backend` was relative to the workspace root, so with `working-directory: backend` it resolved to `backend/backend`.
- Believed: the test file needed editing.
- Actual: the CI env var needed an absolute path. Fixed with `PYTHONPATH: ${{ github.workspace }}/backend`.
- Second failure: `react-hooks/set-state-in-effect` ESLint rule fired on `setState` inside `useEffect`. Disabled in `eslint.config.js` with a documented decision.
- Third failure: `aquasecurity/trivy-action@0.24.0` did not resolve. The release tags carry a `v` prefix, so `0.24.0` / `0.28.0` do not exist. Fixed with `@v0.36.0`.

## Day 7
- Broke: ingress unreachable from Windows — `curl civicpulse.local` returned "Connection refused" on port 80.
- Believed: ingress-nginx was not installed.
- Actual: the kind cluster was created without `extraPortMappings`, so host port 80 was never bound to the node. Recreated with `kind-config.yaml` mapping 80 and 443.
- Broke: `/api/stats` returned 404 through the ingress.
- Believed: backend route path was wrong.
- Actual: `rewrite-target: /$2` on the Ingress stripped the `/api` prefix, so the backend received `/stats` and FastAPI returned 404. Removed the annotation and switched to `pathType: Prefix`.
- Broke: `/api/stats` returned 500 after fixing the path.
- Believed: database was down.
- Actual: `k8s/base/secret.yaml` had no `DATABASE_URL` key, so the backend defaulted to `CHANGE_ME:CHANGE_ME`. Added `DATABASE_URL` and `REDIS_URL` to the Secret, with dev values supplied by a `k8s/overlays/dev/secret.yaml`.
- Broke: after fixing the Secret, Postgres rejected `civicpulse` with `password authentication failed`.
- Believed: the Secret had not propagated.
- Actual: Postgres reads `POSTGRES_USER` and `POSTGRES_PASSWORD` only on first initialisation. The data directory already existed with `CHANGE_ME` credentials from the first cluster setup. Changing the Secret does not update an already-initialised database.
- Fixed: deleted the `postgres` StatefulSet and its PVC (`pgdata-postgres-0`), then reapplied. The StatefulSet recreated the PVC from `volumeClaimTemplates`, and Postgres re-initialised with the current Secret values.
- Also: `secretGenerator` with `behavior: replace` failed with "does not exist; cannot merge or replace" because the base Secret lacked namespace metadata. Switched to a dev-only Secret file listed under `resources:`.
- Also: the ConfigMap duplicated `DATABASE_URL` and `REDIS_URL`, so two sources defined the same env var. Removed them from the ConfigMap; the Secret is now the single source.
- Also: `alembic upgrade head` inside the pod needed `cd /app && PYTHONPATH=/app` — same lesson as CI on Day 6.
- Also: VPA admission controller stuck on missing `vpa-tls-certs` secret; upstream `deploy/` has no certgen Job. Skipped — `vpa-recommender` alone is enough for `updateMode: Off`.

## Day 8 — HPA lag

Load started at t=0 via `k6 run load.js` (200 VUs, 4 min, `POST /api/complaints` with the rules provider and randomized text). Replicas stayed at 2 for the first ~30 seconds even though load was already arriving. The first scale event appeared once CPU crossed the 60% target: the HPA went to 3 replicas at roughly t=60s, then to 5 replicas at roughly t=90s. Total lag between offered load rising and capacity arriving: about 60 seconds to the first new Ready replica, and about 90 seconds to reach full scale.

Where the time went: metrics-server scrapes the kubelet on a ~15 s interval, so the CPU spike was not visible to the HPA instantly; the HPA controller syncs every ~15 s, so it took another cycle to react; then the new pod had to schedule, mount its volumes, pull the image (already cached on the node, so negligible here), and pass its readiness probe before it counted as capacity. Sum: ~30 s of measurement delay, ~30 s of control-loop delay, and the remainder in scheduling and startup.

What would reduce it: a shorter metrics-server scrape interval (e.g. `--metric-resolution=10s`), a lower `--horizontal-pod-autoscaler-sync-period` (default 15 s), a faster readiness probe with a shorter `initialDelaySeconds`, and pre-pulled images on every node. Note that none of these remove the lag — autoscaling is reactive, so it can never replace capacity planning for the first minute of a spike.

## Day 8 — VPA/HPA conflict

VPA runs in recommender mode (`updateMode: Off`) because it and the HPA act on the same CPU signal. If VPA were in `Auto` mode, it would adjust each pod's CPU request based on observed usage. Because the HPA computes utilisation as `usage ÷ request`, raising the request lowers the computed utilisation and the HPA scales **in**; fewer pods then raise per-pod load, so VPA raises the request again; the two controllers oscillate and the deployment never settles.

Keeping VPA in recommender mode turns it into an advisory tool: it produces `Target`, `Lower Bound`, and `Upper Bound` for each container, and a human decides when to apply them. That is the current industrial practice for exactly this reason. The trade-off is that recommendations are not applied automatically — a deliberate choice, because the cost of a feedback loop between two controllers is higher than the cost of an occasional manual update.

Our observed recommendation for the backend container was:

- Target:  cpu 25m, memory 250Mi
- Lower:   cpu 25m, memory 250Mi
- Upper:   cpu 53m, memory 612443531 (bytes — VPA prints memory without a unit; dividing by 1024² gives ~584 Mi)

We applied the Target to `k8s/base/backend.yaml`'s `resources.requests.cpu` and `resources.requests.memory` in a separate commit. If the recommender later reports a different target, that is expected — it is adapting to real usage, and the loop is: read the recommendation, decide, update the manifest, commit.

## Redis volume justification (§2.4)

Redis does two jobs in CivicPulse. The stats cache could be rebuilt from Postgres
freely — losing it costs one extra database query. But the rate-limit counters
and the 24 h LLM triage cache hold real cost: the limiter is the only thing
standing between one bored user and our entire daily Groq quota, and the triage
cache saves inference for duplicate complaints (a burst main gets reported by
nine neighbours). If Redis restarted empty, a caller could reset their own rate
limit and re-spend inference quota. Persisting AOF is therefore cheap insurance
against a class of abuse and cost, not a way to preserve reproducible state.