# Task W12-server-guard — protect the self-hosted server: rate limits and job backpressure

Branch: `feat/server-guard`. Work in `services/api/`, `services/worker/`, and minimal display changes in
`apps/web/src/lib/api/` (+ the component that shows API errors). Small changes to `docker-compose*.yml`,
`.env.example`, `docs/selfhost.md`, `docs/specs/api.md` are allowed.

## Why

Since 2026-10-01 the game API is public and runs on the owner's laptop (`docs/selfhost.md`): browser →
`tsuyulabo.vercel.app` (Vercel rewrites `/v1/*`) → Tailscale Funnel → `127.0.0.1:8000` (Docker: api, worker,
postgres, redis). The laptop's CPU cools poorly, api and worker are capped at 2 CPUs each, and brain simulations are
CPU-heavy. `docs/security-review.md` ("Redis によるレート制限") already lists what is missing: there is no rate
limiting at all, so one script can create unlimited guests (each gets 300 しずく and DB rows), flood Shiori, or queue
brain experiments until the machine is saturated. arq also runs up to 10 jobs at once by default.

## What to build

1. **Redis rate limiter** (`services/api/.../services/ratelimit.py` or similar): atomic Redis counters or a token
   bucket shared by all API processes, injectable for tests (fakeredis or an in-memory implementation behind the
   same interface — follow how the app already injects Redis/queues). On limit: `429` with `Retry-After` and the
   existing error shape (`{"error": {"code": "rate_limited", "message": <Japanese>, "details": {"retry_after": n}}}`).
   If Redis is unavailable, fail **open** for reads and normal play but keep a small in-process fallback limit for
   guest creation; log it. Limits come from settings with sane defaults, e.g.:

   | target | key | default |
   | --- | --- | --- |
   | `POST /v1/auth/guest` | client IP + a global daily cap | 5/hour/IP, 200/day total |
   | `POST /v1/shiori/...` asks | user | 10/min, 100/day |
   | brain experiments, behaviour, activity (incl. GET) | user | 20/min |
   | puzzle issue/submit, daily circuit start/submit | user | 60/min |
   | friends add / lab / like / gift | user | 30/min |
   | everything else authenticated | user | 300/min |

2. **Client IP behind the proxies**: requests arrive via Vercel and Tailscale Funnel, so the socket peer is the Docker
   gateway. Read `X-Forwarded-For` with a configurable number of trusted proxy hops (`TRUSTED_PROXY_HOPS`, default
   suited to Vercel → Funnel; inspect what Funnel actually adds and document it). Spoofing by calling the Funnel URL
   directly can only dodge per-IP limits, not the global caps — document that trade-off in `docs/selfhost.md`.
3. **Job backpressure**: limit in-flight brain/Shiori jobs per user (e.g. 2) and in total (e.g. 20 queued); beyond
   that return `503` `server_busy` with `Retry-After` instead of enqueueing. Make the worker's concurrency
   configurable (`WORKER_MAX_JOBS`, default 2 in `docker-compose.selfhost.yml`) so CPU-bound jobs do not thrash the
   2-CPU cap; keep the existing job timeout behaviour.
4. **Web**: show a friendly Japanese message for `rate_limited` / `server_busy` (「少し時間をおいてから、もう一度ためしてね」
   style, matching existing UI copy) and do not auto-retry them in a tight loop (respect `Retry-After`).
5. **Tests**: limiter unit tests (window rollover, per-key isolation, Retry-After, Redis-down behaviour), API tests for
   429/503 on representative endpoints, IP extraction with 0/1/2 hops and malformed headers, worker setting. Existing
   tests must keep passing with limits that do not interfere (e.g. disabled or high in the test settings).
6. **Docs**: `docs/specs/api.md` (429/503 contract), `docs/selfhost.md` (limits, env vars, how to change them),
   `.env.example`. Mark the item in `docs/security-review.md` as implemented, with what remains.

The host CPU cools poorly: run targeted tests (`uv run pytest services/api -k ...`, `services/worker`) while
developing and the full `services/api` suite once at the end.

## Done when

- `uv run pytest services/api services/worker services/shiori` passes, `uv run ruff check .` is clean,
  web `npm.cmd run lint`, `typecheck`, `test` pass.
- Many small atomic commits (limiter core, settings, IP extraction, per-route limits, guest caps, job backpressure,
  worker concurrency, web messages, docs — each separate, tests with their code).
