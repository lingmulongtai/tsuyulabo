# Task W4-e2e — Playwright: play a whole week through the real stack

Branch: `feat/e2e`. Work in `apps/web/e2e/`, `apps/web/playwright.config.ts`, `apps/web/package.json`
(dev dependency `@playwright/test` + scripts), and `.github/workflows/` (a new `e2e.yml`).

Goal: prove the alpha loop works end to end in a browser: guest → receive egg → temperature → meal →
advance the dev clock (dev panel buttons) → training → cleaning → … → day 7 night → presentation → eclosion →
the adult appears in `/team` / `/adults/[id]`.

- Use the dev time panel (`NEXT_PUBLIC_DEV_TOOLS=1`) to move time. For puzzles, drive the real UI where it is
  practical (tap the temperature stop button, tap three times for cleaning, drag one meal piece); where solving in
  the browser is impractical (the training circuit), read the issued params from the network response and drive
  the pointer along a solved path (write the solver in the test helpers).
- Keep one "golden path" spec (~2–4 minutes) and one short smoke spec (home renders, egg can be received).
- Config: base URL from `E2E_BASE_URL` (default `http://localhost:3000`); API at `NEXT_PUBLIC_API_URL`.
- CI `e2e.yml`: on workflow_dispatch and nightly — `docker compose up -d --build` (postgres, redis, migrate,
  api, worker), start the web app (`npm run build && npm run start` with the env), run Playwright, upload the
  report and traces as artifacts. Do not run it on every push (too slow).
- Document how to run locally in `docs/infra.md` (short section).

## Done when

The specs are written and pass against a running local stack if one is reachable from your sandbox; if Docker is
not reachable, make sure `npx playwright test --list` works and say clearly in your report that the specs were
not executed. Atomic commit plan entries.
