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

## Browser end-to-end tests

The Playwright suite uses the real API and a fresh guest per test. The short smoke spec receives
an egg; the golden path plays all seven research days, both circuit sizes, cleaning, temperature,
pupation, presentation, and eclosion, then checks the same adult in `/team` and `/adults/[id]`.
It plays four real 30-second meals (other meal slots can count as care misses), so allow about
2–4 minutes. It does not require a particular random reward or rank. Time advances only through
the visible dev panel; the circuit solver reads public puzzle parameters from the UI's response.

From the repository root, in PowerShell:

```powershell
npm.cmd ci
npx.cmd playwright install chromium
$env:TSUYU_DEV_TOOLS = '1'
$env:NEXT_PUBLIC_DEV_TOOLS = '1'
$env:NEXT_PUBLIC_API_URL = 'http://localhost:8000'
docker compose up -d --build postgres redis migrate api worker
npm.cmd run build -w @tsuyulabo/web
npm.cmd run start -w @tsuyulabo/web
```

In another terminal at the repository root:

```powershell
$env:E2E_BASE_URL = 'http://localhost:3000' # optional; this is the default
$env:NEXT_PUBLIC_API_URL = 'http://localhost:8000'
npm.cmd run test:e2e -w @tsuyulabo/web
npm.cmd run test:e2e:smoke -w @tsuyulabo/web # just the quick smoke spec
npm.cmd run test:e2e:helpers -w @tsuyulabo/web # circuit solver unit tests
npm.cmd run test:e2e:report -w @tsuyulabo/web
```

An existing `docker compose up` or host dev server also works with both dev-tool flags enabled.
Public environment values must be set before building Next.js, and the runner's API URL must
match that build. For a different web origin, configure API `CORS_ORIGINS` accordingly. Tests
leave their guest records in the development database; they never reset shared data.
On Unix use `npm` / `npx` and `export`. If the sandbox cannot write the browser cache, set
`PLAYWRIGHT_BROWSERS_PATH` to a directory inside `.codex-runs/` for both install and test commands.

Without a stack, validate discovery with `npm.cmd run test:e2e -w @tsuyulabo/web -- --list`
(equivalent to `npx.cmd playwright test --list` from `apps/web`). Discovery does not execute tests.
HTML reports live in `apps/web/playwright-report/`; failed tests retain screenshots, videos, and
traces in `apps/web/test-results/`. Open a trace with `npx.cmd playwright show-trace <trace.zip>`.

`.github/workflows/e2e.yml` runs only on manual dispatch and nightly at 18:23 UTC (03:23 JST).
It builds the Compose backend, builds/starts the web with dev tools enabled, runs the suite, and
uploads reports, failure traces, and service logs for 14 days even on failure. It uses no paid
provider credentials. Browser installation and reporting follow the
[Playwright CI guidance](https://playwright.dev/docs/ci).

## README screenshots and play video

The media suite is an explicit opt-in, separate from smoke/nightly CI. The default Playwright
config ignores `capture.spec.ts`; `e2e/capture.config.ts` selects only the `capture` project.
Start the real local stack above with both dev-tool flags enabled, then run from the root:

```powershell
npm.cmd ci
# In a restricted sandbox, set this for both installation and capture:
$env:PLAYWRIGHT_BROWSERS_PATH = "$PWD/.codex-runs/browsers"
npx.cmd playwright install chromium
npm.cmd run capture -w @tsuyulabo/web
```

Allow about 15 minutes. A fresh guest plays all 21 meal slots, 18 three-star training puzzles,
four perfect cleanings, and two perfect temperature games. Meal placements use the shared game
engine and training uses the golden-path circuit solver. Timing is calculated from public puzzle
parameters with Playwright's clock; submissions still wait for real elapsed time and are scored
by the API. No API responses, ranks, rewards, or game records are fabricated. Pupation follows
Shiori's public hint, which is only 70% reliable by design; its actual hit/miss is recorded.
The capture fails if the presentation is below gold, training is below three stars, or timing
care is below 100 points. Each guest remains in the development database.

Thirteen scenes are saved in both color schemes at a **390 × 844 viewport, device scale 2**
(780 × 1688 pixels). Each pair captures the same state, including a meal line clear, a partial
training path, and sugar-scenario brain playback. Development overlays are hidden for the media;
game content is unchanged. `sharp`, already installed by the locked Next.js dependency, encodes
the screenshots as WebP. The command checks 26 images, each under 150 KB and total under 3 MB.

- Publishable images: `docs/media/screens/<scene>-<light|dark>.webp`.
- Publishable video: `docs/media/playthrough.webm`, a silent 75-second highlight edit, under 8 MB. Needs a full FFmpeg (set `FFMPEG_PATH`); Playwright's bundled FFmpeg lacks the `image2pipe` muxer, so without it only the raw recording is kept.
  Playwright recordings do not include Web Audio. The edit omits repeated meal waits, opens with
  day 3, and slows short actions/reveals so viewers can follow them. All frames come from the video.
- Ignored raw video: `eval-results/media/playthrough-raw.webm`.
- Ignored capture summary: `eval-results/media/capture.json` (rank, points, pupation result,
  image names, and chapter timestamps); failure traces are in `eval-results/media/playwright/`.

The encoder reuses Playwright's installed FFmpeg, including its minimal Windows build, without
adding dependencies. It decodes real video frames, selects the chapter windows from `capture.json`,
and encodes them at 24 fps; retain that summary with its matching raw recording.
`FFMPEG_PATH` can select an already installed alternative. If no usable
encoder is available, the command reports the raw recording's path and leaves it outside git;
do not claim a new published video was generated. To rerun encoding without playing again:

```powershell
node apps/web/e2e/helpers/encode-media.mjs
```

Review all light/dark images and the video before publishing; random puzzle layouts, rewards,
adult traits, and Shiori's configured provider can change the output. The gallery uses the local
stack and development time travel, and does not imply a deployed public service.

## Web Push and the offline PWA

Push uses standard VAPID Web Push through `pywebpush` (no Firebase project needed).
`PushSender` in `services/api/src/tsuyulabo_api/services/push.py` is the provider interface
for a future Capacitor/FCM implementation. The API and worker must share the same VAPID
settings and database. Generate keys locally from the repository root:

```powershell
.\.tools\uv.exe sync
.\.tools\uv.exe run python services/api/scripts/generate_vapid.py --subject mailto:you@example.com
.\.tools\uv.exe run alembic -c services/api/alembic.ini upgrade head
```

The helper appends `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY` (base64url DER), and
`VAPID_SUBJECT` to the ignored root `.env`, preserves existing settings, and refuses to
overwrite existing VAPID entries. It never prints the keys. Keep the private key in your
deployment's secret store; do not commit `.env`. Use a real contact URI in production.
Keep keys stable: rotating the key pair requires browsers to unsubscribe and subscribe again.
Without both keys the public-key endpoint returns null and the worker skips push jobs.

Migration `0010` currently follows `0008` because this clone does not contain the parallel
`0009` migration. The commander must change its `down_revision` to `0009` during integration.

Start Redis, the API, the worker, and the web in separate terminals from the repository root:

```powershell
$env:REDIS_URL = 'redis://localhost:6379/0'
.\.tools\uv.exe run uvicorn tsuyulabo_api.main:app --reload --port 8000
# In another terminal (set REDIS_URL there too):
.\.tools\uv.exe run arq tsuyu_worker.main.WorkerSettings
# In another terminal:
$env:NEXT_PUBLIC_API_URL = 'http://localhost:8000'
npm.cmd run dev -w apps/web
```

Open `http://localhost:3000`, start a research week, then use the home header's **設定** link.
Press **この端末で通知を受け取る** and accept the browser prompt. Merely visiting the app
never requests notification permission. Category and quiet-hour preferences apply to all
of the user's devices; disabling notifications unregisters only the current browser.
The authenticated subscription and preference mutations use the usual `Idempotency-Key`.
Routes are `GET /v1/push/public-key`, `POST`/`DELETE /v1/push/subscribe`, and
`GET`/`PUT /v1/push/preferences`. Subscription endpoints accept browser `toJSON()` output.

Meal jobs begin at **04:00, 12:00, 18:00 JST**. They check active weeks and submitted meal
care events, respect selected slots, and send **ごはんの時間です** linking to `/care/meal`.
Day 7 night also sends **羽化の夜です** linking to `/presentation`. Game eligibility uses
the user's existing dev offset; scheduling and quiet hours always use real JST.
The default **23:00–07:00** quiet interval suppresses the 04:00 reminder, without a deferred
07:00 send. Equal start/end times disable quiet hours. Friend likes, gifts, and eclosions
are checked once a minute and link to `/friends`; only unread events from the last five
minutes and after device registration are eligible. Quiet-hour events are not queued
for later delivery.

Failed deliveries retry each minute through minute 4 of the slot, with a five-minute push
TTL. Persistent per-device event claims prevent repeated/concurrent cron sends; a process
crash after claiming can lose that reminder (best-effort, not exactly-once delivery).
404/410 deletes the subscription and its claims. Other failures retain subscriptions.
Claims older than eight days are pruned. Provider URLs and encryption secrets are never
logged. Endpoint validation allows HTTPS browser push services under FCM, Mozilla, Apple,
and Windows Push; redirects are disabled. Add and review any new provider hostname in
`validate_endpoint` before supporting additional browsers.

To test without waiting for the cron, use DevTools → Application → Service Workers → Push
with this payload after registration:

```json
{"title":"ごはんの時間です","body":"研究室でごはんを作ろう。","url":"/care/meal","tag":"local-test"}
```

This tests display and click routing, not provider delivery. To exercise real encryption
and delivery, with the API stopped against a local test database, run the worker function
from a Python console using `Settings`, `create_engine`, `session_factory`, `WebPushSender`,
and `send_reminders(sessions, sender, now=<aware JST slot boundary>)`; choose a boundary
within the test user's active week and temporarily disable quiet hours. Do not use simulated
timestamps against a production database. Unit tests inject a fake sender:

```powershell
.\.tools\uv.exe run pytest services/api/tests/test_push_routes.py services/api/tests/test_push_provider.py services/worker/tests/test_push.py
npm.cmd run test -w apps/web -- src/lib/push-browser.test.ts src/lib/service-worker.test.ts
```

For offline testing, load the app once online and wait until `/sw.js` is activated. Switch
DevTools Network to Offline, then reload or navigate to an app URL. The cached Japanese
offline shell should appear, with a link to try the home page again. Reconnect and follow
that link to return to live data. Only `/offline.html` is cached: account data, API responses,
and mutations are never cached or replayed. Bump `tsuyu-offline-v1` when changing the shell;
the next service-worker activation deletes only older Tsuyu offline caches. `/sw.js` is
served with no-cache headers and registered with `updateViaCache: 'none'`.

Use HTTPS outside localhost, with an HTTPS API and matching `CORS_ORIGINS`. For local HTTPS
use `npm.cmd run dev -w apps/web -- --experimental-https` and configure the API accordingly.
On iOS/iPadOS, install to the home screen before enabling notifications. Browser and OS
notification permissions must both permit alerts; verify real delivery on each target device.
Implementation references: the installed Next.js 16 `dist/docs/01-app/02-guides/progressive-web-apps.md`
and the [pywebpush provider documentation](https://github.com/web-push-libs/pywebpush).

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
