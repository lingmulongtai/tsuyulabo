# Tsuyu Labo game API

Run commands from the repository root. Python dependencies are already part of the uv workspace.

```powershell
.\.tools\uv.exe sync
.\.tools\uv.exe run alembic -c services/api/alembic.ini upgrade head
.\.tools\uv.exe run uvicorn tsuyulabo_api.main:app --reload
```

With uv on PATH, the server command is `uv run uvicorn tsuyulabo_api.main:app --reload`.
OpenAPI is at `/openapi.json`, interactive docs at `/docs`, and health at `/healthz`.
Startup does not create tables: apply migrations before sending game requests.

## Configuration

Environment variables (or an untracked root `.env`) configure `Settings`:

| Variable | Default | Meaning |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite+aiosqlite:///./tsuyulabo.db` | Async SQLAlchemy URL; Postgres uses `postgresql+asyncpg://...` |
| `REDIS_URL` | unset | Optional health check; required in queue mode |
| `JWT_SECRET` | local development placeholder | Set a random secret of at least 32 bytes before deployment |
| `TSUYU_DEV_TOOLS` | `false` | `1` enables time controls; otherwise every dev route returns 403 |
| `BRAIN_MODE` | `inline` | `inline` or `queue` |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | JSON array of allowed web origins |

`/healthz` returns `status`, `database`, and `redis`. An unconfigured Redis is `disabled`;
a configured dependency failure gives HTTP 503 without exposing connection details.

## Foundation endpoints

| Method | Route | Purpose |
| --- | --- | --- |
| POST | `/v1/auth/guest` | `{ "display_name": "ゆうき" }` → `{ user, token }`, HTTP 201 |
| GET / PATCH | `/v1/me` | Profile and balances; patch display name, title, or favorite adult |
| GET | `/v1/clock` | UTC server/game timestamps, JST slot, 04:00 day boundary |
| GET | `/v1/dev/time` | Clock and `dev_time_offset_s` |
| POST | `/v1/dev/time/advance` | `{ "hours": 3 }` or `{ "to": "next_slot" }` / `next_day` / `eclosion` |
| POST | `/v1/dev/time/reset` | Reset the user's offset |
| GET | `/v1/jobs/{id}` | Owner-only job status, result, error, and timestamps |

Every mutation, including guest creation and PATCH, requires an `Idempotency-Key` UUID.
Keep the same key when retrying; use a new key for each new action. Authenticated routes require
`Authorization: Bearer <token>`. Guest JWTs use HS256, a user ID subject, and a 90-day real-time expiry.
Game-time advances do not extend tokens or change the 24-hour idempotency retention period.

Guest registration creates an eight-character friend code and grants 300 shizuku through the ledger.
The three balance fields are `shizuku`, `research_points`, and `kohaku`; kohaku transfers are disabled
in alpha. `research_rank` is currently `null`: the specs do not yet define its progression formula.
Favorite adults must belong to the authenticated user. Null clears the title or favorite adult.

## Game endpoints

The app registers weeks, puzzles, sleep, adults, team, inventory, home, friends, notifications,
zukan, odds, fly behavior/experiments, and Shiori memo/ask routes described in `docs/specs/api.md`.
`GET /v1/home` aggregates current state and available care; `GET /v1/weeks/current` includes the
seven daily event records. A fly ID is either the active week ID or an owned adult ID.

Puzzle submit bodies are the submission objects directly, not wrapped in a `submission` field.
Issue time and the ten-minute expiry use the real injectable server clock; dev advances affect
game windows, not the wall-clock anti-cheat check. An issued puzzle cannot cross its research day
(or its meal slot). Repeated issue requests do not reserve extra care quota: submit checks it again.

Team changes settle gathering first. Removed adults keep their bags and fractional progress in
`adults.gathering`; adding them again restores the bag without crediting time spent off the team.
Collection transfers materials, shizuku and experience, preserving fractional shizuku/items.

The existing presentation rules intentionally return negative rewards for negative point totals.
These are ledger debits and can return `insufficient_funds` at eclosion; this branch does not change
that game-economy rule. The commander should resolve whether negative rewards should be clamped.

## Transactions and worker integration

- Use `APIRouter(route_class=IdempotentRoute)` for new mutation routers, and obtain sessions through
  `get_session`. The route owns the transaction: handlers must flush as needed and must not commit.
  Business changes and the JSON response record commit together before the response is sent.
- A unique `(user_id, key)` reservation handles simultaneous retries across processes. Status and JSON
  body replay across routes for the same user/key, as specified. Guest registration uses the reserved
  anonymous scope `00000000-0000-0000-0000-000000000000`, since there is no authenticated user yet.
  Expired records are pruned on the next mutation. Expected error responses are cached after rolling
  back business changes; unexpected exceptions roll back the entire transaction and can be retried.
- Ledger `get_account`, `transfer`, `add_material`, and `remove_material` participate in the caller's
  transaction. Transfers lock accounts in ID order, check cached balances against entries, and write
  one debit and one credit sharing a transaction ID. Only `system:*` accounts can have negative balances.
- SQLite connections enable foreign keys and explicit `BEGIN IMMEDIATE` transactions, with a 30-second
  busy timeout. This serializes local database access and makes savepoint/rollback behavior reliable.
  Postgres uses row locks and database uniqueness constraints.
- Inject a clock through `create_app(settings, clock_source=...)` or override `get_clock` in tests.
  The isolated JST helpers in `services/timeutil.py` are temporary W1 helpers for replacement by
  `domain/clock.py`. Advancing to a boundary rounds up to the next second because offsets are integers.
- `create_app(..., brain_handlers={"learn": callable})` registers inline Python handlers. Each takes
  a JSON parameter object and returns a JSON result object; async handlers are also supported.
  `app.state.brain_client.submit(user_id, kind, params)` persists a job, commits it, then dispatches.
  Call this convenience method outside a route-owned transaction. The brain package is still being
  implemented independently. The game app registers `brain.experiment` in inline mode.
- Queue mode enqueues arq `run_brain_job(job_id, kind, params)` with `_job_id=job_id`. The W2 worker
  must implement that function and update the committed job row. Status values are `pending`,
  `running`, `succeeded`, and `failed`. This task implements the enqueue side only.
- Game routes persist `jobs.params` in the same transaction as accepted effects, then dispatch after
  commit. SQL and Redis are not one atomic transaction: process termination between commit and
  enqueue can leave a pending job. Its persisted kind/params are sufficient to redispatch; a periodic
  recovery scan belongs to the worker. Explicit enqueue failures produce `failed/enqueue_failed`.
- In queue mode, training waits up to three seconds after committing the accepted care event. A fast
  result includes `association` and `learning_status: completed`; otherwise the response includes a
  `job_id`, `association: null` and `learning_status: pending`. Poll `/v1/jobs/{id}` for completion.
  The first finalized HTTP response remains immutable for idempotency replay, including pending
  responses. Training workers apply pending events in sequence order and tolerate redelivery.
  Learning that finishes after eclosion also updates the adult's brain and cached preferences.

Worker handler registration (the worker itself is outside this branch):

| Job kind | Handler contract |
| --- | --- |
| `brain.experiment` | `services.experiments.handler(session_factory, brain_adapter)` returns an async JSON handler; stores an experiment with a user-scoped sequence and `display_id: c-<seq>` |
| `brain.training` | `services.training.handler(session_factory, brain_adapter)` applies accepted training, updates puzzle/care results, and completes associated jobs |
| `shiori.answer` | Receives `{user_id, question, game_now}`; the Shiori worker supplies the answer handler |

Both Python handler factories are in the `tsuyulabo_api` package. Job inputs are internal: the public
job endpoint does not expose brain snapshots or RNG seeds. Daily memo readers expect
`ShioriMessage.role == "memo"`, with `created_at` in the user's game-time day (04:00 JST boundary).

## Brain boundary

`brain_adapter.py` imports only `tsuyu_brain.api`, lazily. Without that independently developed
package, brain-dependent requests return `503 brain_unavailable`; tests inject a deterministic fake.
The façade must expose `default_params` as well as the six functions in W1-brain item 9.
`generate_individual` parameters must be a dataclass or a JSON-compatible mapping.

The interim persistence codec stores individual-generation arguments and seeded training history
(at most 18 events), then reconstructs through public façade calls. It avoids depending on an
unpublished engine byte codec. The commander can replace it with the engine's finalized codec at
integration; no brain internals are imported and the brain package is untouched.

## Migrations and tests

```powershell
.\.tools\uv.exe run alembic -c services/api/alembic.ini upgrade head
.\.tools\uv.exe run alembic -c services/api/alembic.ini revision --autogenerate -m "describe change"
.\.tools\uv.exe run pytest services/api
.\.tools\uv.exe run ruff check services/api
.\.tools\uv.exe run ruff format --check services/api
.\.tools\uv.exe run python services/api/scripts/export_openapi.py
```

Alembic reads `DATABASE_URL` through the same settings as the application. Programmatic migration
callers can set `config.attributes["database_url"]`. The initial migration creates all 20 specified
tables; embeddings use `vector(384)` on Postgres and JSON on SQLite. Postgres needs pgvector available
and permission to create the `vector` extension. Learned weights use a portable binary column.

Tests use a fresh temporary SQLite database per test, HTTPX ASGI clients, and frozen clocks. Coverage
includes concurrent retries/spending, ledger rollback, authentication, errors, dev controls, job
ownership, migration upgrade/downgrade and schema parity, and offline Postgres migration SQL.
Redis/arq enqueue is mocked; live Postgres and Redis integration remains for W2 infrastructure tests.

The full-week HTTP scenario solves all puzzles, presents at gold or better, ecloses, gathers for
eight hours, collects and levels up. A second scenario neglects days 2–5 and verifies stable care
misses and normal rank. Queue tests cover the three-second deadline, late adult updates and replay.
The export command writes `apps/web/src/lib/api/openapi.json` without starting the app or loading
the brain engine. Mutation headers are part of the live and exported OpenAPI schema.
