# Task W1-web-puzzles — client puzzle engines and sound (TypeScript)

Branch: `feat/web-puzzles`. Work only in `apps/web/src/game/` (new folder). Do not touch other parts of
`apps/web` (the commander is building the design system and screens there in parallel).

Read first: `AGENTS.md`, `docs/specs/puzzles.md` (source of truth), and the `<script>` at the end of
`docs/spec/kikakusho-v0.2.html` (the planning demo: zip puzzle logic, Web Audio `Sound` object,
eclosion odds) — port its ideas, not its DOM code.

Next.js here is v16 (see `apps/web/AGENTS.md`), but this task is plain TypeScript with no React.
Run `npm.cmd install` at the repo root first. Tests: `npm.cmd run test -w @tsuyulabo/web`
(vitest, config at `apps/web/vitest.config.ts`, test files `*.test.ts` next to the code).
Typecheck: `npm.cmd run typecheck -w @tsuyulabo/web`. Do not add dependencies.

## Build (all pure, framework-free, strict TS, no `any`)

1. `game/puzzles/types.ts` — types for every kind's `params`, `submission`, and verify result, matching
   puzzles.md field names exactly (snake_case where the JSON uses it). `InvalidReason` union with the
   shared reason codes.
2. `game/puzzles/meal.ts` — shapes table, an immutable-style engine usable by the UI:
   `createMealGame(params)`, `currentHand(state)`, `canPlace(state, p, r, c)`, `place(state, p, r, c, t)`
   → `{ state, placedCells, clearedRows, clearedCols, clearedCells (with ingredient), moveScore, combo }`,
   `hasAnyMove(state)`, `isOver(state, elapsedMs)`, and `verifyMeal(params, submission)` that replays a
   whole submission exactly like the server.
3. `game/puzzles/training.ts` — zip/circuit engine for pointer-drag UIs: `createTrainingGame(params)`,
   `tryStep(state, cell)` (start only on k=1, adjacency, no revisit, checkpoint order, stepping back onto the
   previous cell pops), `truncateTo(state, cell)`, `isSolved(state)`, `starsFor(n, elapsedMs)`,
   `verifyTraining(params, submission)`, and helpers `neighbors(n, cell)`, `cellToRC`, `rcToCell`.
4. `game/puzzles/cleaning.ts` — `markerPosition(params, tMs)`, `gradeTap(params, tMs)`,
   `verifyCleaning(params, submission)`.
5. `game/puzzles/temperature.ts` — `needleTemp(params, tMs)`, `scoreTemperature(params, stopMs)`,
   `verifyTemperature(params, submission)`.
6. `game/puzzles/index.ts` — re-exports.
7. `game/audio/sound.ts` — a small Web Audio synth (lazy `AudioContext`, resume on first user gesture,
   global mute stored in memory with a setter): `tone`, `arp`, `chord`, and named cues used by the game:
   `step(n)` (pentatonic rising "pop"), `bad()`, `place()`, `lineClear(lines)`, `combo(n)`,
   `puzzleClear()` (arpeggio), `star(i)`, `greatSuccess()` (fanfare), `omen(tier)` (rising with tier
   0..3), `mutation()` (jingle), `drumroll()` + `rankReveal(rank)`, `tap()`, `perfect()`.
   Must be SSR-safe (no `window` access at import time). Plus `game/audio/haptics.ts` with `buzz(pattern)`
   guarded for SSR and unsupported browsers.
8. `game/expectation.ts` — the shared expectation colours (white < blue < gold < rainbow) as tokens:
   `TIERS = [{ id: "white", label: "白", color: "#FFFFFF" }, { id: "blue", ..."#7FC8FF" },
   { id: "gold", ..."#FFD54A" }, { id: "rainbow", ... }]` and helpers mapping a week rank / tier index to a tier.

## Tests

- Unit tests for every engine function, including every `InvalidReason`.
- `game/puzzles/fixtures.test.ts`: loads every JSON under `packages/fixtures/puzzles/<kind>/` (resolve from
  the repo root with `node:fs` / `node:path`; skip gracefully if the folder has no files yet — another agent
  is generating them in parallel) and checks `verify*` against `expected`.
- Hand-written cases mirroring the puzzles.md examples: double clear with row+col intersection counted once,
  combo multiplier chain and reset, theme bonus, hand dealing in groups of 3, time limit grace 1500 ms.

## Done when

- vitest passes, typecheck passes, `npm.cmd run lint -w @tsuyulabo/web` is clean for `src/game/`.
- Commit plan entries are atomic (types; each engine + its tests; sound; haptics; expectation; fixtures runner).
