# Task W6-review — security and correctness review of the game API (with fixes)

Branch: `fix/api-review`. Work in `services/api/` and `services/worker/` (tests + fixes). **No database migration**
(another task adds migration 0008 in parallel) — if a fix truly needs a schema change, write it up instead.

Review the whole API with the plan's principles in mind (企画書 §14 「ずるを防ぐしくみ」, `docs/specs/api.md`):
server clock only, server-side puzzle verification, double-entry ledger, idempotency, ownership.

Look for and fix (each fix = a failing test first, then the fix, as separate or combined atomic entries):
- Authorisation: every route that takes an id (adults, weeks, jobs, flies, friends, races, daily circuit, breeding
  parents) must check ownership / friendship; no IDOR. Friend lab view must not leak private fields.
- Idempotency: same key + different body must not replay a different request silently (return 409 or
  `idempotency_key_reused`); keys scoped per user; concurrent duplicates.
- Ledger: no negative balances, no reward without an event, clamped rewards, level-up and gifts atomic; balance cache
  equals the ledger sum after the full-week scenario.
- Puzzles: replaying a submission for another user's puzzle, submitting after expiry, submitting twice, forged
  timestamps, huge payloads (cap move/path/taps lengths), NaN/inf numbers.
- Dev tools: every `/v1/dev/*` route is disabled unless `TSUYU_DEV_TOOLS`, and the time offset cannot move backwards
  into an inconsistent state.
- JWT: algorithm pinned, expiry enforced, secret length validated at startup in production.
- Rate limits / abuse: document (do not necessarily build) where Redis rate limits are needed.
- Shiori: user-supplied question cannot inject tool calls that read other users' records.

Deliverables: fixes + tests, and `docs/security-review.md` (Japanese) listing what was checked, what was fixed, and
what remains as recommendations. Done when: `uv run pytest`, ruff pass. Atomic commit plan entries.
