# AGENTS.md — rules for coding agents (Codex, Claude, subagents)

Read this first. Then read `docs/DEVELOPMENT_PLAN.md` and the spec for your area in `docs/specs/`.

## Project

ツユラボ (Tsuyu Labo): a weekly fruit-fly raising / research game whose fly behaves according to a small spiking brain model.
Monorepo: Next.js web (`apps/web`), FastAPI game API (`services/api`), PyTorch brain engine (`services/brain`),
Shiori agent (`services/shiori`), arq worker (`services/worker`), shared JSON fixtures (`packages/fixtures`).

The specs in `docs/specs/` are the source of truth. If you must deviate, update the spec in the same branch
(separate commit, `docs(spec): ...`) and explain why in your final message.

## Commits — ATOMIC, ALWAYS

The owner cares about this more than anything else.

- One commit = one logical change. Many small commits are expected (a feature is usually 5–30 commits).
- Commit as you go. Do not batch a whole task into one commit at the end.
- Every commit must leave the repo in a working state (tests you touched pass, code imports).
- Tests go in the same commit as the code they test, or in the commit right after.
- Conventional Commits, English, imperative, lower-case subject, no period:
  `feat(api): add idempotency key middleware`, `test(brain): cover lif refractory period`,
  `chore(web): add vitest config`, `refactor(domain): extract slot helpers`, `docs(spec): clarify combo scoring`.
  Scopes: `web`, `api`, `domain`, `brain`, `shiori`, `worker`, `infra`, `ci`, `fixtures`, `spec`.
- Add this trailer to every commit you create:
  `Co-Authored-By: Codex <codex@openai.com>` (Codex) or the Claude trailer (Claude).
- Never rewrite history that is already on `main`. Never force-push `main`.
- Do not commit secrets, `.env`, build output, `node_modules`, `.venv`, or large data files.

## Python

- Python >= 3.12, uv workspace at the repo root (`pyproject.toml`). Each service is a package with a `src/` layout.
- Run things with `uv run ...` from the repo root (e.g. `uv run pytest services/brain`).
- Style: ruff (lint + format, line length 100), type hints everywhere, `from __future__ import annotations`.
- Tests: pytest (+ pytest-asyncio for the API). Keep unit tests fast (< 30 s per package); mark slow ones `@pytest.mark.eval`.
- Pure logic stays pure: `services/api/src/tsuyulabo_api/domain/` must not import the DB, FastAPI, or Redis.

## TypeScript / web

- npm workspaces. Next.js App Router, strict TypeScript, ESLint, vitest for unit tests, Playwright for E2E.
- Game logic that must match the server lives in `apps/web/src/game/` as plain TS (no React) with vitest tests.
- UI text is Japanese. Code identifiers and comments are English.

## Working style for agents

- Stay inside the directories your task names. If you need a change elsewhere, keep it minimal and mention it.
- Prefer small, readable modules over clever ones. Match the surrounding code.
- Before finishing: run the relevant tests and linters, make sure `git status` is clean (everything committed).
- Finish with a short report: what you built, commit list, how to run it, anything left undone or uncertain.
- Append a short entry to `docs/HANDOFF.md` under "Log" describing what your task finished (as its own commit).
