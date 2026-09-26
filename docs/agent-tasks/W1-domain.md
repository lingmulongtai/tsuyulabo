# Task W1-domain — pure game rules and puzzles (Python)

Branch: `feat/game-domain`. Work only in `services/api/src/tsuyulabo_api/domain/`,
`services/api/tests/domain/`, and `packages/fixtures/` (plus a HANDOFF.md log entry at the end).

Read first: `AGENTS.md`, `docs/specs/game-rules.md`, `docs/specs/puzzles.md`. These are the source of truth.

**The domain package must stay pure**: standard library only (dataclasses, enum, random, datetime, zoneinfo,
math). No FastAPI, SQLAlchemy, Redis, or brain imports. Functions take explicit inputs (times, seeds, prior
state) and return new values. Another agent is building the DB/API layer in parallel and will call these.

## Build

1. `constants.py` — every number from the specs (slots, decay rates, rank thresholds, odds table, traits,
   subskills, level caps, shapes and weights, cue/valence lists, skill unlock table, pupation-site text pools,
   economy constants). Names in English, Japanese display names alongside.
2. `clock.py` — JST, 04:00 day boundary, `slot_of(dt)`, `game_day(dt)`, `research_day(week_start, now)`,
   `weekday_label(research_day)`, `next_slot_start(dt)`, helpers for iterating slots between two times.
3. `lifecycle.py` — `stage_at(week_start, now)`, `ready_to_eclose`, which actions are available when
   (`action_availability(week_start, now, usage) -> list[TodoItem]` with status done/available/locked and
   `available_at`), per-slot / per-day usage limits (game-rules.md §3).
4. `stats.py` — lazy decay of hunger/cleanliness from `last_computed_at` to `now` (frozen during egg/pupa,
   start values at hatch), mood + label, hunger-zero tracking; meal / cleaning effects.
5. `care_miss.py` — evaluate care misses for the elapsed period given the event log (§5). Must be
   idempotent: evaluating the same period twice must not double count (return the set of miss keys, e.g.
   `("meal", day, slot)`, so the caller can store them).
6. `puzzles/` — one module per kind: `meal.py`, `training.py`, `cleaning.py`, `temperature.py`,
   `pupation_site.py`. Each has `generate(rng, context) -> (params, secret)`, `verify(params, submission)
   -> VerifyResult(valid, reason, score fields...)`, and where relevant `roll(rng, ...)` for luck
   (great success, hirameki, hit). Exact scoring and `reason` codes from puzzles.md. Training generator:
   random Hamiltonian path on n×n (Warnsdorff + random tie-break + restart), checkpoints as specified.
7. `presentation.py` — weekly points breakdown and rank from the event log (§6), rewards.
8. `eclosion.py` — odds per rank with the temperature / pupation adjustments, tier roll, stars, strain,
   sex, two traits with exclusivity rules, `omen_sequence` including the optional fake-out (§7).
9. `adults.py` — level caps, level-up cost, exp thresholds, subskill unlock and roll at 10/25/50.
10. `team.py` — lazy gathering for a team member from `last_computed_at` to `now` (§9): items/hour, energy
    decay and factor, bag cap, material weights from learned preferences (input: dict cue→value), shizuku,
    rare drop with rng. Deterministic given rng seed.
11. `sleep.py` — sleep duration, bonus, energy recovery (§10).
12. `friends.py` — friend code generation (alphabet without 0 O 1 I) and validation.

## Fixtures

`packages/fixtures/puzzles/<kind>/*.json` in the format at the end of puzzles.md: for meal, training,
cleaning, temperature — at least 6 valid and 6 invalid cases each (cover every `reason` code), hand-checked
edge cases (double line clear with row+col intersection, combo chains, theme bonus, time limits).
Write a small generator script `services/api/scripts/gen_puzzle_fixtures.py` that builds them with the
domain code, and a pytest that re-verifies every fixture file against the domain code.
Add `packages/fixtures/README.md` explaining the format (the TypeScript side will consume these).

## Tests

`services/api/tests/domain/` — thorough unit tests for every module: slot boundaries at 03:59/04:00/11:59/
12:00/17:59/18:00, research day rollover, stage transitions (hatch on day 1 night, molt, pupa, eclosion
window), decay math, care-miss idempotency, every puzzle rule and reason code, odds sum to 100 after
adjustments, eclosion determinism with seed and statistical sanity (10k rolls within tolerance), team
gathering caps and energy, level caps.

## Done when

- `uv run pytest services/api/tests/domain` passes and `uv run ruff check services/api` is clean.
- Many atomic commits (a module + its tests per commit, fixtures separately). HANDOFF.md Log entry at the end.
