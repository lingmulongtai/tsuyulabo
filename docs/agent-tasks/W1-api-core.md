# Task W1-api-core — game API foundation (FastAPI)

Branch: `feat/api-core`. Work in `services/api/` **except** `src/tsuyulabo_api/domain/` and
`tests/domain/` (another agent is writing the pure game rules there in parallel — do not create or edit
files in those folders). Plus a HANDOFF.md log entry at the end.

Read first: `AGENTS.md`, `docs/specs/api.md` (principles, auth, errors, data model), `docs/specs/game-rules.md`
§1 (time) and §11 (economy).

Dependencies are already declared in `services/api/pyproject.toml`; avoid adding new ones.

## Build

1. `settings.py` — pydantic-settings: `DATABASE_URL` (default `sqlite+aiosqlite:///./tsuyulabo.db`),
   `REDIS_URL` (optional), `JWT_SECRET`, `TSUYU_DEV_TOOLS` (bool), `BRAIN_MODE` (`inline|queue`), CORS origins.
2. `app.py` — `create_app(settings)` factory, `/healthz`, CORS, error handlers producing the error format in
   api.md (`{"error": {"code", "message", "details"}}`), including validation errors → `validation_error`.
   `tsuyulabo_api.main:app` for uvicorn.
3. `db/` — async engine/session factory, SQLAlchemy 2 typed models for **all** tables in api.md's data model
   (portable types so SQLite works in tests; JSON columns; `LargeBinary` for learned weights; the pgvector
   `papers.embedding` column only on Postgres — keep SQLite working, e.g. a TypeDecorator falling back to JSON).
4. Alembic — `services/api/alembic.ini`, `migrations/`, an initial migration matching the models; async env.
5. `auth/` — `provider.py` interface, guest provider: `POST /v1/auth/guest` creates a user (+ friend code,
   + initial 300 shizuku via the ledger), returns a JWT (HS256, `sub`, 90 days). `get_current_user`
   dependency. `GET /v1/me`, `PATCH /v1/me`.
6. `services/clock.py` — game time = server UTC now + user's `dev_time_offset_s`; an injectable clock
   (tests freeze time). `GET /v1/clock` (use simple local helpers for JST/slot for now; the domain agent's
   `domain/clock.py` will replace them in W2 — keep the helper small and isolated in `services/timeutil.py`).
7. `services/idempotency.py` — dependency/middleware requiring `Idempotency-Key` on mutating routes;
   stores status + JSON body per (user, key); replays on repeat; 24 h retention; concurrent duplicate safety
   (unique constraint). Error `idempotency_key_required`.
8. `services/ledger.py` — double-entry ledger: accounts per (owner, currency), `transfer(session, from, to,
   amount, reason, ref)` in one transaction, balances cached and verified; `insufficient_funds`. Inventory
   helpers for materials (add/remove with checks).
9. `routers/dev.py` — `/v1/dev/time`, `/v1/dev/time/advance` (`hours`, or `to: next_slot|next_day`),
   `/v1/dev/time/reset`; 403 `dev_tools_disabled` unless `TSUYU_DEV_TOOLS`.
10. `services/jobs.py` — `jobs` table helpers + a `BrainClient`/`JobQueue` abstraction with `inline` mode
    (call a Python function directly) and `queue` mode (arq enqueue; just the enqueue side). `GET /v1/jobs/{id}`.
11. `services/api/README.md` — how to run (`uv run uvicorn tsuyulabo_api.main:app --reload`), env vars,
    migrations, tests.

## Tests

`services/api/tests/` (not `tests/domain/`): pytest + pytest-asyncio + httpx `AsyncClient` with an
in-memory/temporary SQLite DB per test. Cover: health, guest auth + me, JWT rejection, error format,
idempotency replay and missing key, ledger double-entry invariants and insufficient funds, dev time
advance + disabled 403, clock endpoint with frozen time, alembic upgrade head on SQLite.

## Done when

- `uv run pytest services/api --ignore=services/api/tests/domain` passes and `uv run ruff check services/api` is clean.
- Many atomic commits (settings; app factory; each model group; migration; each service; each router;
  tests with their code). HANDOFF.md Log entry at the end.
