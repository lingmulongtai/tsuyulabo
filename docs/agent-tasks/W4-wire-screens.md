# Task W4-wire-screens — connect the commander's screens to the API

Branch: `feat/wire-screens`. Work in `apps/web/`.

The API client and hooks (`src/lib/api/*`) exist now. These screens still run on local demo data and must be
connected to the real endpoints **without changing their look** (keep the components; change the pages and add
small props only where needed):

- `src/app/care/training/page.tsx` — `TeachPicker` → `POST /v1/puzzles {kind:"training", cue, valence}` →
  `TrainingGame` with the server params → submit → `ResultSheet` with the server's `stars`, `hirameki`,
  `association.value` (show the new preference as a bar: 苦手 −1 … +1 好き) and `skill_unlocked` if present.
  Show remaining trainings today from `/v1/home` todo. Practice mode at `?practice=1` and as offline fallback.
- `src/app/presentation/page.tsx` — `GET /v1/weeks/current/presentation` → `PresentationBoard` (keep the demo
  at `?demo=1`). Only reachable when the week is `ready_to_eclose`; otherwise show a friendly "まだ" card.
- `src/app/eclosion/page.tsx` — real eclosion: `POST /v1/weeks/current/eclose` when the player presses
  「羽化させる」 (pass the response into `EclosionStage` as `result`, mapping the API fields to
  `EclosionResult`), then 「飼育室へ」 goes to `/adults/<new id>`. Keep the odds table from `GET /v1/odds` and the
  demo at `?demo=1`.
- Home: when `week.ready_to_eclose` is true, show a prominent 「研究発表会へ」 card linking to `/presentation`
  (use the existing card/button primitives; a gold glow is welcome). At night (`clock.slot === "night"`) pass
  `night` to `Terrarium`.
- `src/components/art/BehaviorFly.tsx` exists: use it on `/adults/[id]` with `GET /v1/flies/{id}/behavior`.

Also: vitest tests for the API→component mapping helpers you add (e.g. eclosion response → `EclosionResult`).

## Done when

lint, typecheck, test and build pass. Atomic commit plan entries (one per screen).
