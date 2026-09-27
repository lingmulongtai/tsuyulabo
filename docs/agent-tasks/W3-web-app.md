# Task W3-web-app — API client, data hooks and the remaining screens

Branch: `feat/web-app`. Work in `apps/web/`.

Read first: `AGENTS.md`, `apps/web/AGENTS.md` (Next.js 16 — read the relevant docs in
`node_modules/next/dist/docs/` before using an API you are unsure about), `docs/specs/api.md`,
`docs/specs/game-rules.md`, and the existing design system: `src/app/globals.css` (tokens),
`src/components/ui/*`, `src/components/shell/*`, `src/components/home/*`, `src/components/games/CareFrame.tsx`
and `MealGame.tsx` (look and feel to match), `src/game/*` (engines, sound, haptics, labels, practice).

**Do not create or edit** (the commander is building these in parallel):
`src/components/games/TrainingGame.tsx`, `src/components/eclosion/**`, `src/components/presentation/**`,
`src/app/care/training/**`, `src/app/eclosion/**`, `src/app/presentation/**`, `src/components/art/**`.

## Build

1. **API client.** Add `openapi-typescript` (dev) and `openapi-fetch`; script `npm run gen:api` that generates
   `src/lib/api/schema.d.ts` from `src/lib/api/openapi.json` (already exported by the API). A small client
   (`src/lib/api/client.ts`) with base URL `NEXT_PUBLIC_API_URL` (default `http://localhost:8000`), bearer token,
   automatic `Idempotency-Key` (UUID per logical action, reused on retry), and typed errors using the API's
   error format. Guest bootstrap: on first visit call `POST /v1/auth/guest` and keep the token in
   `localStorage` (guarded; SSR-safe).
2. **Data layer.** Add `@tanstack/react-query`; a `Providers` client component in the root layout; hooks in
   `src/lib/api/hooks.ts` for every endpoint in api.md (home, weeks, presentation, eclose, puzzles
   issue/submit, sleep, adults, level-up, team, collect, inventory, zukan, odds, friends, like, gift,
   notifications, shiori memo/ask + job polling, brain behavior/experiments, dev time). Invalidate `home`
   after every mutation. Replace `src/lib/types.ts` contents with aliases over the generated schema types
   (keep the exported names so existing components compile).
3. **Wire existing screens.** `src/app/page.tsx` renders `HomeScreen` from `useHome()` with loading and error
   states (skeleton in the same style; a friendly offline card with a retry button). When there is no active
   week, show a "卵を受け取る" call-to-action (`POST /v1/weeks`) with the egg art. `src/app/care/meal/page.tsx`:
   issue a real `meal` puzzle, play it with `MealGame`, submit, and show the server result in `ResultSheet`
   (great success from the server). Keep the practice mode reachable at `/care/meal?practice=1` and fall back to
   it with a notice when the API is unreachable.
4. **New screens** (same visual language — rounded cards, chunky buttons, tokens, Japanese UI text):
   - `/care/cleaning` — bottle tapping timing game (`src/game/puzzles/cleaning.ts`): a vial that shakes, a
     marker bouncing across a zone bar, three taps, per-tap grade popups (PERFECT / GOOD / MISS), sound + haptics.
   - `/care/temperature` — a thermometer / dial needle swinging (`temperature.ts`), one stop button, score.
   - `/care/pupation` — three option cards with Shiori's hint bubble, pick one, reveal hit/miss.
   - `/care/sleep` — おやすみ / おはよう with a night-sky / morning card, sleep duration and bonus.
   - `/team` — team slots (max 5), bag contents, collect button with a satisfying reveal, adult picker
     (from `/v1/adults`), level-up with shizuku.
   - `/adults/[id]` — adult detail: art (`Tsuyu` with strain/sex), stars, traits, subskills, likes/dislikes
     (preference bars), special skills, level, and a "なんで？" button that opens Shiori ask.
   - `/zukan` — behaviour and strain collection grid with locked silhouettes and completion %.
   - `/friends` — friend code (copy), add by code, list, lab view (`/friends/[id]`), like / gift, notifications.
   - `/shiori` — ask Shiori: question input, job polling, answer with evidence ID chips and the AI badge and the
     "ゲーム内のモデルで測った結果です" note.
   - A floating **dev time panel** (only when `NEXT_PUBLIC_DEV_TOOLS=1`): current game time, buttons for next
     slot / next day / to eclosion / reset.
5. Tests: vitest for the client (idempotency key reuse, error parsing, token bootstrap with mocked fetch) and
   for any pure helpers you add.

## Done when

`npm.cmd run lint`, `npm.cmd run typecheck`, `npm.cmd run test`, `npm.cmd run build` all pass (the build
must not need the API to be running). Atomic commit plan entries (dependency adds, generator, client, each
hook group, each screen).
