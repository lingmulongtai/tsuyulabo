# Infrastructure

## Local stack with Docker

Install Docker with the Compose plugin, start its engine, then run from the repository root:

```sh
docker compose up
```

No `.env` file or separate install/migration command is required. Compose builds the Python
images, starts PostgreSQL 16 with pgvector and Redis 7, runs Alembic once, and starts the API,
worker, and Next.js dev server. The API and worker wait for successful migrations and healthy
Redis; the web server waits for the API healthcheck. The agreed application entrypoints must
be present (the other W2 branches supply them).

- Web: <http://localhost:3000>
- API health: <http://localhost:8000/healthz>
- OpenAPI: <http://localhost:8000/docs>

All published ports bind to loopback. PostgreSQL and Redis persist in named volumes. Web source
is mounted from the repository, while Linux dependencies and `.next` use separate volumes to
avoid mixing them with host installations. `npm ci` runs each time the web container starts.
Python source is baked into images; after changing it, run `docker compose up --build`.

```sh
docker compose config --quiet       # Validate without contacting the Docker engine
docker compose logs -f api worker
docker compose down                # Stop; retain data
```

`docker compose down --volumes` also deletes database, queue, and web cache volumes; use it only
when intentionally resetting local data. Copy `.env.example` to `.env` only to override defaults.
If changing database credentials, update both `POSTGRES_*` and `DATABASE_URL`; initialization
variables do not change credentials in an existing PostgreSQL volume.

## Run services on the host

Install Python 3.13, uv, Node.js 22, PostgreSQL 16 with pgvector, and Redis 7. Start PostgreSQL
and Redis locally and create a `tsuyulabo` database owned by `tsuyu`. Alternatively, use
`docker compose up -d postgres redis` for just those two dependencies.

From the repository root, in PowerShell:

```powershell
$env:DATABASE_URL = 'postgresql+asyncpg://tsuyu:tsuyu-dev-only@localhost:5432/tsuyulabo'
$env:REDIS_URL = 'redis://localhost:6379/0'
$env:JWT_SECRET = 'tsuyulabo-local-development-only-change-in-production'
$env:TSUYU_DEV_TOOLS = '1'
$env:BRAIN_MODE = 'queue'
$env:CORS_ORIGINS = '["http://localhost:3000"]'
uv sync --frozen
uv run alembic -c services/api/alembic.ini upgrade head
uv run uvicorn tsuyulabo_api.main:app --host 0.0.0.0 --port 8000 --reload
```

In another terminal with the same backend environment:

```powershell
uv run arq tsuyu_worker.main.WorkerSettings
```

For a simpler backend-only setup, `BRAIN_MODE=inline` runs brain work inside the API. Keep the
worker when using queued Shiori/background jobs. In a third terminal:

```powershell
$env:NEXT_PUBLIC_API_URL = 'http://localhost:8000'
$env:NEXT_PUBLIC_DEV_TOOLS = '1'
npm.cmd ci
npm.cmd run dev
```

On Unix shells use `export NAME=value` and `npm` instead. In the Codex Windows clone, replace
`uv` with `.\.tools\uv.exe`; use `npm.cmd` / `npx.cmd` to avoid PowerShell shim restrictions.
A root `.env` is consumed by Compose; these host commands explicitly set their environment.

## Environment variables

These are local defaults, not deployment secrets. Compose passes the backend variables to both
API and worker (and migration). CORS uses a JSON array for the settings parser.

| Variable | Local default | Purpose |
| --- | --- | --- |
| `POSTGRES_USER` | `tsuyu` | Database initialization user |
| `POSTGRES_PASSWORD` | `tsuyu-dev-only` | Development database password |
| `POSTGRES_DB` | `tsuyulabo` | Database name |
| `DATABASE_URL` | `postgresql+asyncpg://tsuyu:tsuyu-dev-only@postgres:5432/tsuyulabo` | Async SQLAlchemy connection; use `localhost` on the host |
| `REDIS_URL` | `redis://redis:6379/0` | Queue connection; use `localhost` on the host |
| `JWT_SECRET` | `tsuyulabo-local-development-only-change-in-production` | Local JWT signing key; replace for deployment |
| `TSUYU_DEV_TOOLS` | `1` | API time/debug tools; set `0` in production |
| `BRAIN_MODE` | `queue` | `queue` for Compose/production; `inline` for simple local tests |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Allowed web origins |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Browser-accessible API URL, never Compose's `api` hostname |
| `NEXT_PUBLIC_DEV_TOOLS` | `1` in Compose, `0` in production image | Display development controls |
| `ANTHROPIC_API_KEY` | empty | Optional real Shiori provider credential |
| `OPENAI_API_KEY` | empty | Optional real Shiori provider credential |

Shiori defaults to MockProvider; local startup and CI need no paid provider credentials.
The web Dockerfile accepts `NEXT_PUBLIC_API_URL` and `NEXT_PUBLIC_DEV_TOOLS` as build arguments:
Next.js embeds public values at build time, so changing runtime environment alone is insufficient.
The runtime listens on `HOSTNAME=0.0.0.0`, `PORT=3000`; Next telemetry is disabled in containers.

## Production images

All build contexts are the repository root:

```sh
docker build -f services/api/Dockerfile -t tsuyulabo-api .
docker build -f services/worker/Dockerfile -t tsuyulabo-worker .
docker build -f apps/web/Dockerfile -t tsuyulabo-web --build-arg NEXT_PUBLIC_API_URL=https://api.example.com .
```

Python images use uv with the frozen workspace lock, package-specific dependencies, and
non-editable installs; dev dependencies and uv stay out of the Python 3.13-slim runtime.
The workspace's Linux torch source selects CPU wheels. Both runtime images use UID 10001.
The API also carries Alembic files and checks `/healthz`; the migration container disables that
HTTP healthcheck. The worker runs `arq tsuyu_worker.main.WorkerSettings`.

The Node 22-slim image contains standalone output, static assets, and public assets, and runs
as `node`. It sets `NEXT_PRIVATE_STANDALONE=1` only during the build, using the default supported
by the locked Next.js 16 version without editing `apps/web/next.config.ts`. This is an internal
Next flag: verify it when upgrading. An explicit equivalent line inside `nextConfig`, if needed,
is `output: process.env.NEXT_PRIVATE_STANDALONE === "1" ? "standalone" : undefined,`.
The build checks that the monorepo entrypoint `apps/web/server.js` was generated. See the
[Next.js standalone output documentation](https://nextjs.org/docs/app/api-reference/config/next-config-js/output)
and [uv Docker guide](https://docs.astral.sh/uv/guides/integration/docker/).

## CI and evaluation reports

`.github/workflows/ci.yml` runs on pushes and pull requests:

| Job | Checks |
| --- | --- |
| `python` | Cached uv, `uv sync --frozen`, `uv run ruff check .`, `uv run pytest`; default pytest config excludes `eval` |
| `web` | Node 22/npm cache, `npm ci`, lint, typecheck, unit tests, production build |
| `api-postgres` | pgvector/PostgreSQL 16 service, migrations, API tests with `DATABASE_URL`; temporarily `continue-on-error: true` |

`.github/workflows/eval.yml` runs on pull requests and manual dispatch. It runs
`uv run pytest -m eval`, `uv run python -m tsuyu_brain.eval`, and
`uv run python -m tsuyu_shiori.eval`. Each command runs even when an earlier evaluation fails.
CI uses Shiori's default mock and supplies no provider secrets.

Each module must write `eval-results/<brain|shiori>/report.json` and `report.md`.
**The JSON contract is a top-level boolean `passed`.** A value of `false` fails the job; missing
or invalid reports, missing/empty Markdown, and failed commands also fail it. Only `passed: true`
with successful commands passes. Modules may exit nonzero and still write useful reports.

Reports upload as the `eval-results` artifact for 14 days even after a failure. Same-repository
PRs get one comment containing both Markdown reports, updated using `<!-- tsuyulabo-eval -->`.
Long reports are truncated only in the comment; artifacts retain the full content. Fork and
Dependabot PRs still run evaluations and upload artifacts but cannot post using their read-only
tokens. A repository policy denying comment writes produces a warning, not an evaluation failure.
The workflow uses `pull_request`, never `pull_request_target` to execute contributed code.

## Future deployment

The [project proposal](spec/kikakusho-v0.2.txt) plans Vercel for the web, Cloud Run for API and
workers, a small managed PostgreSQL such as Neon, and Redis such as Upstash for the portfolio
release. These workflows validate and report; they do not deploy.

Before adding deployment, connect the managed services, provide production secrets, disable
both dev-tool flags, set exact CORS origins and the web's public API build value, and run Alembic
as a release step before API/worker rollout. Keep the Redis-polling arq worker running with CPU
available outside HTTP requests; select a suitable Cloud Run worker execution model and scaling
policy when implementing that deployment. Configure the API's Cloud Run container port as 8000.
Add image publishing, PR preview environments, and deployment workflows in that phase.

The proposal's beta phase moves toward an always-running Cloud Run instance, Cloud SQL, Redis,
Cloud Scheduler, and Sentry. Later phases add autoscaling, database redundancy/read replicas,
CDN delivery, and moving brain computation toward the client.
