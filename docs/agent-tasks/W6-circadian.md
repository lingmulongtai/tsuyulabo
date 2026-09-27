# Task W6-circadian — いっしょにねる: circadian gauge (Phase 2)

Branch: `feat/circadian`. Work in `docs/specs/game-rules.md`, `services/api/`, `apps/web/`. **No database
migration** (another task adds migration 0008 in parallel): compute everything from the existing `sleep_sessions`.

企画書 §9: 「毎日同じくらいの時間にねると『体内時計ゲージ』がたまり、チームのげんきが回復する。ハエの体内時計はノーベル賞
（2017年）につながった研究の題材でもある。」

1. Spec (own `docs(spec)` commit, add §10b to game-rules.md): gauge 0–100 from the last 7 sleep sessions — regularity
   of bedtime and wake time (circular standard deviation in minutes over clock time), plus a bonus for 6–9 h
   duration; effects: energy recovery multiplier 1.0–1.3 and a small shizuku bonus at wake when the gauge ≥ 80.
   Explain the real biology in one paragraph (period, timeless, clock neurons) with a 本物 note.
2. Pure domain function with thorough tests (wrap-around at midnight!). API: include `circadian: {gauge, streak,
   typical_bedtime, typical_wake}` in `/v1/home` and in the `/v1/sleep/end` result; apply the multiplier to team energy
   recovery. Re-export OpenAPI and regenerate web types.
3. Web: on `/care/sleep` show the gauge as a moon-phase style ring with typical times, and a small ring on the home
   header; an explanation sheet with Shiori's short note (and the 本物 badge for the clock-gene fact). Match the
   design system.

Done when: `uv run pytest`, web lint/typecheck/test/build pass. Atomic commit plan entries.
