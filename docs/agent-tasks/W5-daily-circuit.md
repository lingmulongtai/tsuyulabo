# Task W5-daily-circuit — 今日の回路: one shared puzzle a day, friend time ranking (Phase 2)

Branch: `feat/daily-circuit`. Work in `docs/specs/`, `services/api/`, `apps/web/`.

企画書 §4/§6: 「全員に同じ問題が出る大きめの回路パズル。フレンドの中でタイムを競う」, reward しずく.

1. **Spec** (`docs/specs/puzzles.md` new section §6 and `game-rules.md` note): daily puzzle = the training
   circuit rules on a 7×7 board with 9 checkpoints, generated deterministically from the JST date
   (`seed = hash("daily-circuit:" + YYYY-MM-DD)`), same for everyone; one scored attempt per day (practice replays
   allowed without score); reward しずく by time bands (e.g. < 20 s: 60, < 40 s: 40, else 20); ranking among self +
   friends for that day. Commit as `docs(spec)`.
2. **Domain + API**: generator reuse; `GET /v1/daily-circuit` (params for today, my result if any),
   `POST /v1/daily-circuit/submit` (verify path, wall-clock anti-cheat like other puzzles, idempotent, reward via
   ledger), `GET /v1/daily-circuit/ranking` (me + friends, best valid time, ties by submit time). Tests, including
   that two users get the same board and that the board changes at the 04:00 JST boundary. Re-export OpenAPI.
3. **Web**: `/daily` screen reusing `TrainingGame` (it takes `TrainingParams` — adapt with a thin wrapper, do not
   fork it) with a timer, result sheet with rank among friends, a ranking list (avatars = each friend's favourite
   adult art, fallback wild type), and a home entry point (small card 「今日の回路」 with done/not-done state). Add it
   to the friends page too. Match the design system.

Done when: `uv run pytest`, web lint/typecheck/test/build pass. Atomic commit plan entries.
