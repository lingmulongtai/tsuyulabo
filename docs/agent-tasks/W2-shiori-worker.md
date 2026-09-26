# Task W2-shiori-worker — Shiori agent and the arq worker

Branch: `feat/shiori-worker`. Work in `services/shiori/` and `services/worker/` only (read, but do not edit,
`services/api` and `services/brain`).

Read first: `AGENTS.md`, `docs/specs/shiori.md` (source of truth), `docs/specs/api.md` (jobs, experiments,
shiori endpoints, data model), `services/brain/src/tsuyu_brain/api.py`, and the API's db models / job helpers
in `services/api/src/tsuyulabo_api/`.

## Build — `tsuyu_shiori` (must not import the API package; data comes in through small protocols)

1. `gateway/` — `Provider` protocol, `MockProvider` (default; deterministic, template-based, builds answers
   only from the tool results it was given, always cites their IDs), `AnthropicProvider` and
   `OpenAIProvider` over raw `httpx` (Messages API / Responses API; keys from env; model names configurable,
   defaults: a light model for journals, a mid model for Q&A), response cache (in-memory LRU + optional Redis),
   token + cost accounting per call.
2. `records.py` — protocols the host implements: `RecordStore` (care events by week/kind, sleep sessions,
   associations, experiments lookup/exists by ID) and `Lab` (run an odor-choice experiment on a copy of a fly's
   brain state and persist it, returning its ID). Plus in-memory fakes for tests/eval.
3. `tools/` — tool schemas + implementations: `get_care_events`, `get_association`, `run_odor_choice`,
   `search_papers`.
4. `agent/` — the loop (max 4 steps, tool calls, final answer), system prompt with Shiori's promises.
5. `verify/` — sentence splitter for Japanese, ID extraction (`#0412`, `#c-19`), existence check through
   `RecordStore`, drop unsupported sentences, banned-expression check (emotion attributions like 悲しんで /
   うれしがって / 怒って → rewrite or drop), and a verification report (kept / dropped / rate).
6. `rag/` — `data/papers.jsonl` (≈20 short hand-written summaries with real citations: olfactory learning in
   the mushroom body, dopamine PAM/PPL1, giant fiber escape, MN9 proboscis extension, circadian clock / 2017
   Nobel, larval connectome Winding 2023, adult connectomes), BM25 retriever (pure Python), and a pgvector
   retriever interface (embeddings can be a simple hashing embedder for now; document the upgrade path).
7. `features.py` — `morning_memo(...)`, `coach_tip(...)`, `presentation_host(...)`, `answer_question(...)`,
   each returning text + evidence IDs + verification report + cost.
8. `eval.py` — `python -m tsuyu_shiori.eval`: synthesize a week of records with the fakes, auto-generate
   questions with known answers, run the agent with MockProvider, report accuracy, evidence verification
   rate, and cost per answer to `eval-results/shiori/report.{json,md}` with a top-level `"passed"` gate
   (accuracy ≥ 0.8 and verification rate ≥ 0.95 under Mock).

## Build — `tsuyu_worker`

1. `main.py` — `WorkerSettings` for arq (Redis from `REDIS_URL`), functions and cron jobs registered.
2. `adapters.py` — implements Shiori's `RecordStore` / `Lab` on top of the API's SQLAlchemy models and
   session factory (import from `tsuyulabo_api.db`).
3. Jobs: `brain_run_experiment(job_id)`, `shiori_answer(job_id)` (reads the job row, runs
   `answer_question`, writes result/cost/status, stores `shiori_messages`), `shiori_morning_memo(user_id)`.
   Cron: nightly journal/memo generation at 03:30 JST for users active in the last 24 h.
4. Keep job functions callable directly (without Redis) so the API's inline mode and tests can use them.

## Tests

`services/shiori/tests/` (fast, Mock only; verify drops fake IDs, banned expressions, agent loop limits,
BM25 ranking, cache hits) and `services/worker/tests/` (jobs run against a SQLite DB created with the API's
models; no Redis needed). Mark the eval run `@pytest.mark.eval`.

## Done when

`uv run pytest services/shiori services/worker` and `-m eval` pass; ruff clean; `python -m tsuyu_shiori.eval`
writes the report. Atomic commit plan entries.

## Note: the brain engine may not be on main yet

`services/brain` (branch `feat/brain-engine`) is still being written in parallel. If `tsuyu_brain.api` does not
exist in your clone, code against the façade described in `docs/agent-tasks/W1-brain.md` (item 9) through a
thin adapter module in your package (e.g. `brain_adapter.py`) with a deterministic fake used by your tests.
Import `tsuyu_brain.api` lazily inside the adapter so the code runs either way. The commander will wire the
real engine after both branches merge.
