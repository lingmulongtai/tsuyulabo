# Task W19-immersive-ui — the vial fills the screen; the UI floats over it

Branch: `feat/immersive-ui`. Read `docs/specs/vision-v2.md` §3 first (source of truth) and look at
`docs/media/v2/` plus the live site on a phone viewport. W14–W18 are merged; this is the design pass that makes the
whole app feel like vision-v2 instead of "cards with a 3D card inside".

## Review (commander, 2026-10-13, production home on an iPhone 13 viewport)

1. The home is still a stack of light beige cards with the 3D vial as one dark card in the middle. **The vial must be
   full-bleed** (edge to edge, behind the status bar and tab bar) and everything else floats over it.
2. Opaque beige panels ("この子の一週間", "バナナの匂いを置く", "今日のお世話") cover ~40% of the vial. Make overlays small,
   **dark frosted glass** (backdrop blur, 1px light hairline, ~60–70% transparent), grouped in a bottom sheet that rests
   at ~25% height and can be dragged up for the full care list; at rest show only the next 1–2 actions.
3. The weekday chip row is heavy. Replace with a thin 7-step progress line (day dots, the current one glowing amber)
   inside the top overlay.
4. The header crowds 「こんにちは / 1日目（月） / 設定 / おやすみ / 300」. Make a translucent top bar: day + time-of-day on
   the left, icons (sleep, settings, しずく) on the right.
5. At the egg stage nothing is visible in the wide framing. Frame the subject per stage (egg/larva: close on the medium
   surface; pupa: on the glass; adult: wider) and keep it in focus.
6. Move the app to the **dark photographic theme** (ink background, unbleached text, amber accent) for home and all care
   screens; keep a light theme only if it reads equally premium — otherwise follow the system with dark as the
   designed default.
7. Colony, collection (図鑑) and friends should show each individual as a small rendered portrait (reuse the vivarium
   renderer offscreen or cached snapshots), not text cards. Puzzles open as sheets over the dimmed vial so the creature
   stays in view.
8. Motion: overlays fade/slide with a calm spring; respect `prefers-reduced-motion`.

## Done when

- web lint/typecheck/test/build and the Playwright week E2E pass; new phone screenshots of home (each stage), a care
  sheet, colony and collection in `docs/media/v2/`, before/after in the PR-style report.
- Many small atomic commits (tokens, top bar, progress line, bottom sheet, overlay material, per-stage framing, each
  screen, portraits, motion, screenshots — each separate).
