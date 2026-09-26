# Task W2-puzzle-parity — make the TypeScript verifiers match the Python domain

Branch: `fix/puzzle-parity`. Work in `apps/web/src/game/puzzles/` and `docs/specs/puzzles.md` only.

The Python domain (`services/api/src/tsuyulabo_api/domain/puzzles/`) is authoritative. Its interpretations of
the spec are documented in `services/api/src/tsuyulabo_api/domain/README.md`. The shared fixtures in
`packages/fixtures/puzzles/` were generated from it. `apps/web/src/game/puzzles/fixtures.test.ts` currently
fails 8 fixtures:

- training `diagonal_step` (validation order: Python checks length → bounds → revisit → adjacency → start →
  end → checkpoint order → time), training `expired_elapsed` (elapsed cap = puzzle lifetime 600000 ms →
  `time_exceeded`)
- cleaning `good_boundary`, `perfect_boundary` (grade boundaries are inclusive and must be robust to float
  error, e.g. compare with a small epsilon exactly like Python does)
- temperature `expired_elapsed`, `expired_stop`, `fractional_timestamp` (timestamps must be integers; a
  non-integer is `non_monotonic_time`), `half_rounds_up` (rounding rule for the score)

## Do

1. Read the Python verifiers for every kind (meal, training, cleaning, temperature) and mirror their exact
   validation order, integer checks, caps, epsilons and rounding in TypeScript. Check meal too even though
   its fixtures pass.
2. Make every fixture pass; keep the existing unit tests passing (update a unit test only if it encoded the
   old, non-authoritative behaviour — say which in the commit body).
3. Update `docs/specs/puzzles.md` with a short "検証の順番と細かい決まり" section per kind so the two
   implementations cannot drift again (validation order, integer timestamps, 600000 ms cap, inclusive
   boundaries with epsilon, rounding).

## Done when

`npm.cmd run test -w @tsuyulabo/web` passes with 0 skipped fixture suites, typecheck and lint pass.
Atomic commit plan entries (one per kind + the spec update).
