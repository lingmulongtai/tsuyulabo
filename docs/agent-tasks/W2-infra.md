# Task W2-infra — docker compose, Dockerfiles, CI

Branch: `feat/infra`. Work in the repo root config files, `infra/`, `.github/`, and Dockerfiles next to each
service (`services/*/Dockerfile`, `apps/web/Dockerfile`). Do not change application code (other agents are
writing it in parallel); if an entrypoint does not exist yet, reference the agreed name below anyway.

Read first: `AGENTS.md`, `docs/DEVELOPMENT_PLAN.md` (stack, layout, "ローカルで動かす"), `docs/specs/api.md`
(env vars and BRAIN_MODE), `docs/specs/brain.md` ("評価"), `docs/specs/shiori.md` ("評価").

## Agreed entrypoints (being written by other agents)

- API: `uvicorn tsuyulabo_api.main:app --host 0.0.0.0 --port 8000`; migrations `alembic -c services/api/alembic.ini upgrade head`.
  Env: `DATABASE_URL` (postgresql+asyncpg://...), `REDIS_URL`, `JWT_SECRET`, `TSUYU_DEV_TOOLS`, `BRAIN_MODE`, `CORS_ORIGINS`.
- Worker: `arq tsuyu_worker.main.WorkerSettings` (same env as the API).
- Brain eval: `python -m tsuyu_brain.eval` → `eval-results/brain/report.{json,md}`.
- Shiori eval: `python -m tsuyu_shiori.eval` → `eval-results/shiori/report.{json,md}`.
- Web: Next.js 16 in `apps/web` (npm workspace `@tsuyulabo/web`), env `NEXT_PUBLIC_API_URL` (default
  `http://localhost:8000`), `NEXT_PUBLIC_DEV_TOOLS`.

## Build

1. `services/api/Dockerfile` — multi-stage, `ghcr.io/astral-sh/uv` for installing, python 3.13-slim runtime,
   CPU-only torch (the root `pyproject.toml` already routes torch to the PyTorch CPU index on Linux),
   `uv sync --frozen --no-dev --package tsuyulabo-api`, non-root user, healthcheck on `/healthz`.
   `services/worker/Dockerfile` similarly (`--package tsuyu-worker`). Keep images as small as practical;
   use a shared base stage if it helps. Add a root `.dockerignore`.
2. `apps/web/Dockerfile` — Next.js standalone output build (add `output: "standalone"` ONLY via env-driven
   config if needed — prefer documenting the one-line change in your final message rather than editing
   `next.config.ts`), node 22-slim runtime.
3. `docker-compose.yml` — services: `postgres` (`pgvector/pgvector:pg16`, volume, healthcheck), `redis`
   (`redis:7-alpine`), `migrate` (one-shot alembic upgrade, depends on healthy postgres), `api` (depends on
   migrate + redis, port 8000, `TSUYU_DEV_TOOLS=1`, `BRAIN_MODE=queue`), `worker`, `web` (dev mode with the
   repo mounted is fine, port 3000). A `.env.example` at the root with every variable and safe dev defaults.
   `docker compose up` must be the only command needed.
4. `.github/workflows/ci.yml` — on push and pull_request:
   - `python`: setup uv (astral-sh/setup-uv), `uv sync --frozen`, `uv run ruff check .`,
     `uv run pytest` (unit tests; eval marker excluded by default config). Cache uv.
   - `web`: setup node 22 with npm cache, `npm ci`, `npm run lint`, `npm run typecheck`, `npm run test`,
     `npm run build`.
   - `api-postgres`: runs the API test-suite against a Postgres service container (set `DATABASE_URL`
     to postgres; tests should already honour it) — mark `continue-on-error: true` for now.
5. `.github/workflows/eval.yml` — on pull_request and workflow_dispatch: runs brain eval and shiori eval
   (`uv run pytest -m eval` + the eval modules), uploads `eval-results/` as an artifact, and posts/updates a
   single PR comment with both Markdown reports (use `actions/github-script`, find the previous comment by a
   hidden marker `<!-- tsuyulabo-eval -->`). Fail the job if the reports say a gate failed (the report JSON has
   `"passed": false` at the top level — document that contract in the workflow comments).
6. `docs/infra.md` — how to run locally (compose, and without Docker: `uv run uvicorn ...` + `npm run dev`),
   env vars table, CI jobs overview, and the future Cloud Run / Vercel deployment plan from the spec.

## Checks

- `docker compose config` must succeed (Docker may not be running; if `docker` is unavailable, validate YAML
  with a quick Python yaml load and say so in your report).
- Workflows must be valid YAML (validate with Python). Use pinned major versions of actions.

## Done when

Commit plan entries are atomic (one per Dockerfile, compose, env example, each workflow, docs).
