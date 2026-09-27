# Task W5-deploy — deployment configs so the owner only needs to log in and add secrets

Branch: `feat/deploy`. Work in `infra/`, `.github/workflows/`, `apps/web/` (config only), `docs/deploy.md`.

The owner will log in to Vercel CLI and (later) a cloud provider. Plan (企画書 §14, ポートフォリオ版): Web on Vercel,
API + worker on Cloud Run, small Postgres (Neon) with pgvector, Upstash Redis. Nothing may be deployed by you —
write configs, scripts and docs, and validate them locally.

1. **Web (Vercel)**: make `apps/web` deployable from the monorepo (root directory `apps/web`, npm workspaces
   install). Add `apps/web/vercel.json` only if needed. `NEXT_PUBLIC_API_URL` from env. Document the exact
   `vercel` CLI commands (link, env add, deploy --prod) in `docs/deploy.md`.
   Also a **"demo without backend" notice**: when `NEXT_PUBLIC_API_URL` is unset in production, the home screen
   shows a friendly card explaining the public demo mode and links to the practice minigames (meal/training
   practice modes and the eclosion/presentation demos already exist) instead of an error.
2. **API + worker (Cloud Run)**: `infra/cloudrun/` with service YAMLs (or `gcloud run deploy` scripts) for
   `tsuyulabo-api` and `tsuyulabo-worker` (worker as a Cloud Run service with min instances 1 or a job — explain
   the trade-off), a migration job, Artifact Registry image build/push script, required env/secrets list
   (DATABASE_URL, REDIS_URL, JWT_SECRET, CORS_ORIGINS, BRAIN_MODE, optional LLM keys) using Secret Manager.
3. **GitHub Actions**: `deploy.yml` (workflow_dispatch only) that builds and pushes images and deploys to
   Cloud Run using Workload Identity Federation (document the one-time setup), plus a Vercel deploy step using a
   `VERCEL_TOKEN` secret. It must be inert until secrets exist (skip with a clear message).
4. **Database**: notes for Neon (enable `vector` extension) and Upstash; `alembic upgrade head` via the
   migration job; a cost table matching the plan (0〜3,000円/月 + LLM).
5. `docs/deploy.md` in Japanese: step-by-step for the owner (what to click / run, which secrets to set, how to
   verify with `scripts/smoke_api.py --base https://...`).

Validate YAML/scripts (actionlint if available, `docker build` of images if Docker is reachable, `next build` with
production env). Done when: configs + docs committed, web build passes. Atomic commit plan entries.
