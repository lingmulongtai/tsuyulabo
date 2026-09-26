# Task W2-api-game — game endpoints (domain + DB + brain)

Branch: `feat/api-game`. Work in `services/api/` (you may make small, well-tested fixes inside
`src/tsuyulabo_api/domain/` if you find a bug — separate commits, `fix(domain): ...`). Do not touch
`services/brain` except to call its public façade (`tsuyu_brain.api`); do not touch `services/shiori`,
`services/worker`, or `apps/web`.

Read first: `AGENTS.md`, `docs/specs/api.md` (every endpoint listed there except the Shiori ones which only
need the job plumbing), `docs/specs/game-rules.md`, `docs/specs/puzzles.md`, the existing code in
`services/api` (settings, db models, auth, clock, idempotency, ledger, jobs, dev router) and the pure rules in
`services/api/src/tsuyulabo_api/domain/`, and `services/brain/src/tsuyu_brain/api.py`.

## Build

1. Replace the temporary time helper with `domain.clock` everywhere (keep the injectable clock service).
2. `services/week.py` + `routers/weeks.py` — start a week (egg), current week with per-day records,
   lazy stat/care-miss evaluation on every read (store `last_computed_at`; idempotent care-miss keys),
   presentation (7th day night), eclose (server RNG → tier, stars, strain, sex, traits, `omen_sequence`;
   create the adult with `tsuyu_brain.api.generate_individual` + `new_fly_state`; rewards via the ledger;
   notification to friends), past weeks list.
3. `routers/puzzles.py` — `POST /v1/puzzles` (availability/limits from `domain.lifecycle`, store params and
   secret, expiry) and `POST /v1/puzzles/{id}/submit` (domain verify, wall-clock anti-cheat, luck rolls,
   effects on stats / growth, `care_events` with a per-user sequential `seq`, training → brain
   `apply_training` on the week's larva brain state (create the larva brain state at week start from default
   params) → association value and skill unlock). Invalid submission → 422 `invalid_submission` with reason.
4. `routers/sleep.py` — `/v1/sleep/start`, `/v1/sleep/end` (bonus via ledger, team energy recovery).
5. `routers/adults.py`, `routers/team.py`, `routers/inventory.py` — list/detail, level-up (ledger), team
   PUT (settle gathering before changes), GET, collect (materials → inventory, shizuku → ledger, exp →
   levels, subskill unlocks), preferences from the adult's brain state (`preference_index` per cue, cached on
   the adult row and refreshed after training).
6. `routers/home.py` — `GET /v1/home` aggregate exactly as in api.md (todo from `domain.lifecycle`).
7. `routers/zukan.py`, `routers/odds.py`, `routers/friends.py` (codes, add/remove, lab view, like, gift,
   notifications) per game-rules.md §12.
8. `routers/brain.py` — `GET /v1/flies/{id}/behavior` (decoder output via `tsuyu_brain.api.predict_behavior`)
   and `POST /v1/flies/{id}/experiments` (enqueue via the existing job abstraction; in inline mode run
   `run_odor_choice` on a copy and store an `experiments` row with a per-user `seq`, shown as `c-<seq>`).
9. `routers/shiori.py` — only the plumbing: `GET /v1/shiori/memo` returns the stored memo for today (or
   null) and `POST /v1/shiori/ask` creates a `jobs` row of kind `shiori.answer` and enqueues it (another agent
   builds the Shiori agent and the worker that fills the result).
10. Every mutating endpoint uses the idempotency dependency. All currency changes go through the ledger.
11. `scripts/export_openapi.py` — writes `apps/web/src/lib/api/openapi.json` (create the folder) so the web
    client can generate types. Run it at the end and include the JSON file in its own commit.

## Tests

- Router-level tests with httpx AsyncClient + SQLite for each endpoint group, including limits and errors.
- **A full-week scenario test**: guest → start week → using dev time advance, play every slot for 7 days with
  valid submissions (write small solvers in the test helpers: greedy placement for meal, the stored secret
  path for training, optimal tap/stop times for cleaning/temperature, the correct pupation option from the
  secret) → presentation rank ≥ gold → eclose → team → advance 8 h → collect → level-up. Also a neglect
  scenario (no care for days 2–5) producing care misses and a normal rank.
- Idempotency replay on puzzle submit (same key → same response, no double reward).

## Done when

- `uv run pytest services/api` passes (the domain tests too), ruff clean, `apps/web/src/lib/api/openapi.json`
  exported. Atomic commit plan entries (one per service/router + its tests).
