# Task W6-maze-race — 迷路レース: the brain decides how your fly runs (Phase 2 flagship)

Branch: `feat/maze-race`. Work in `docs/specs/`, `services/brain/`, `services/api/`, `services/worker/`, `apps/web/`.

企画書 §6: 「同じ迷路に、自分の成虫を送り出す。どこにどの匂いを置くかの作戦を立てると、脳のシミュレーションで走りが決まる。
しつけと特性が効く。」 Weekly, asynchronous, friends ranking. Nothing bought with money affects results.

1. **Spec** `docs/specs/maze-race.md` (own `docs(spec)` commit): weekly maze (e.g. 9×9 grid with walls, start and
   goal) generated from the ISO week (same for everyone); the player places up to 3 odour tokens (cues from the
   training list) on open cells; one entry per week per player (re-entry replaces the previous one); the run is a
   step simulation: at each step the fly senses odour gradients (sum of cue intensities decaying with path distance)
   and light, the brain façade converts that into turn/forward probabilities using the fly's own state (learned
   preferences via `preference_index`, traits like right_turner / light_lover / wanderer via params), max N steps;
   score = steps to goal (or distance left). Deterministic given (maze, placements, fly state, seed = hash of week +
   user). Replay = list of positions/headings per step.
2. **Brain façade**: `tsuyu_brain.api.maze_policy(state, observation) -> {forward, left, right, stay}` probabilities
   built from the existing circuits (steering + olfaction_mb), cheap enough to run ~400 steps in < 1 s. Unit tests:
   a banana-trained fly moves toward banana tokens more often than an untrained one; a right_turner turns right more.
3. **API + worker**: tables via ONE Alembic migration with revision id `0008` and down_revision `0007`;
   `GET /v1/races/current` (maze, my entry, deadline), `POST /v1/races/current/entry` (adult id + placements →
   enqueue a `brain.maze_run` job; inline mode runs it directly), `GET /v1/races/current/ranking` (me + friends),
   `GET /v1/races/entries/{id}/replay`. Worker job registered. Tests incl. determinism and ownership.
4. **Web** `/race`: maze editor (tap a cell to place a token, pick the cue from chips, max 3), choose the adult
   (cards with preferences shown as bars so the strategy is readable), submit, then a replay animation (the fly art
   walking the path on the grid with a step counter, speed control), and the friend ranking. Entry card on home and
   friends pages. Match the existing design system (tokens, `src/components/ui/*`, `Tsuyu` art, `TruthBadge` モデル).
5. Re-export OpenAPI and regenerate web types.

Done when: `uv run pytest`, web lint/typecheck/test/build pass. Atomic commit plan entries.
