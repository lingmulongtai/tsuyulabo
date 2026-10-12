# Task W15-reframe — stop being a "research" game: words, screens and UI material

Branch: `feat/reframe`. Read `docs/specs/vision-v2.md` first: it is the source of truth and overrides older specs.

**Do not touch** `apps/web/src/components/vivarium/**`, `apps/web/src/app/vivarium/**`, or `apps/web/package.json` /
`package-lock.json` (another agent, W14, is building the 3D vivarium there in parallel). Do not change Shiori's
backend `SYSTEM_PROMPT` or Mock templates (the production LoRA model was trained on them); W17 handles Shiori later.

## Goal

The owner said plainly: this is **not a research game**. It is a deep raising game where you feel you are truly keeping
a small living creature. Remove the research framing everywhere a player can see it, and give the UI a quiet,
tactile, photographic material that will sit on top of a photoreal 3D scene (W14) instead of the current cute look.

## What to build

1. **Terminology** — write `docs/specs/terms-v2.md` first (its own commit) with a table old → new, then apply it to all
   user-facing text: web UI copy, page titles, metadata/manifest, notifications/Web Push text, API error messages and
   any server-generated display strings, Android app name/strings, README tagline and screenshots captions.
   Starting point (refine for natural Japanese; keep it warm, plain, not childish):
   研究員さん → 飼い主さん（または呼びかけなし）, 研究所 → 飼育棚, 研究◯日目 → ◯日目, 研究週 → この子の一週間,
   研究発表会 → 羽化の日（育ちの評価と称号）, 研究ランク → 育ちの評価, 研究チーム → コロニー, 研究ポイント → 飼育の経験,
   研究員シオリ → シオリ（飼育を手伝う相棒）, 実験 → ためし（コピーで試す）, 論文 → 図鑑の豆知識.
   Internal identifiers, DB columns, API field names and migrations stay unchanged.
2. **Remove research-looking screens and elements**: evidence-ID chips, raw numbers and graphs as the main content,
   "記録 #0412" style citations in the UI (keep them available behind a small "根拠" disclosure where Shiori answers
   need them), dashboards. Replace with plain sentences about the creature and visible state.
3. **Game explanations**: rewrite onboarding/help/empty states so they explain the raising loop of vision-v2 §4
   (food you mix ends up in the vial, training changes what it likes, cleaning keeps it healthy, temperature changes its
   pace, every individual is different, lines across generations). Short, concrete, no jargon.
4. **UI material** (design tokens in `globals.css` / Tailwind theme, `components/ui/*`, shell/navigation): frosted
   translucent panels over a dark photographic background, thin 1px lines, small precise labels, ink / unbleached /
   amber neutrals with one attention colour, line icons, restrained motion; typography with a refined Japanese face
   (check what is loaded; you may switch to e.g. Noto Serif JP for headings + a clean sans for UI, keep it fast).
   Remove the cartoon character art from the main navigation and headers (keep files if other screens still need them
   until W16 replaces them). The look must feel premium and calm — like a camera app over a macro photo — and stay
   accessible (contrast, focus rings, 44px targets).
5. **Every screen still works**: puzzles, care, eclosion, colony, collection, friends, race, sumo, contest, settings.
   Update tests and Playwright E2E expectations for the new copy.
6. **Screenshots**: re-capture the README / `docs/media` screenshots with the new look (see `docs/infra.md` for the
   capture flow) and update captions.

## Done when

- No player-visible 「研究」 remains (`grep` the web app, API display strings and Android strings; list any intentional
  exceptions in `terms-v2.md`).
- `uv run pytest services/api` (targeted where possible, full once at the end — the host CPU cools poorly),
  `uv run ruff check .`, web `lint`, `typecheck`, `test`, `build`, and the Playwright week E2E pass.
- Many small atomic commits (terms doc, tokens, primitives, shell, then one commit per screen/area, API strings, push
  texts, Android strings, tests, screenshots, docs).
