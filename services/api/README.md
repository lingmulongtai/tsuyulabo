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
| POST | `/v1/dev/time/advance` | `{ "hours": 3 }` or `{ "to": "next_slot" }` / `next_day` |
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

## Transactions and W2 integration

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
  implemented; concrete handler registration belongs to W2.
- Queue mode enqueues arq `run_brain_job(job_id, kind, params)` with `_job_id=job_id`. The W2 worker
  must implement that function and update the committed job row. Status values are `pending`,
  `running`, `succeeded`, and `failed`. This task implements the enqueue side only.
- SQL and Redis are not one atomic transaction. W2 game mutations should create their job row inside
  their transaction and dispatch after commit, using a durable outbox for crash recovery. The current
  convenience client records enqueue failures; process termination between commit and enqueue can
  leave a pending job. Worker retries and the three-second training wait belong to W2.

## Migrations and tests

```powershell
.\.tools\uv.exe run alembic -c services/api/alembic.ini upgrade head
.\.tools\uv.exe run alembic -c services/api/alembic.ini revision --autogenerate -m "describe change"
.\.tools\uv.exe run pytest services/api --ignore=services/api/tests/domain
.\.tools\uv.exe run ruff check services/api
.\.tools\uv.exe run ruff format --check services/api
```

Alembic reads `DATABASE_URL` through the same settings as the application. Programmatic migration
callers can set `config.attributes["database_url"]`. The initial migration creates all 20 specified
tables; embeddings use `vector(384)` on Postgres and JSON on SQLite. Postgres needs pgvector available
and permission to create the `vector` extension. Learned weights use a portable binary column.

Tests use a fresh temporary SQLite database per test, HTTPX ASGI clients, and frozen clocks. Coverage
includes concurrent retries/spending, ledger rollback, authentication, errors, dev controls, job
ownership, migration upgrade/downgrade and schema parity, and offline Postgres migration SQL.
Redis/arq enqueue is mocked; live Postgres and Redis integration remains for W2 infrastructure tests.
