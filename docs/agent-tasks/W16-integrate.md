# Task W16-integrate — the vial is the game: put the 3D vivarium at the centre and wire every care action into it

Branch: `feat/integrate-vivarium`. Read `docs/specs/vision-v2.md` (source of truth), `docs/specs/terms-v2.md` (W15) and
`apps/web/src/components/vivarium/README.md` (W14) first. Both W14 and W15 are merged on `main`.

## Goal

Today the puzzles feel bolted on: you play a puzzle, a number changes somewhere. Make every action land *inside the vial*,
visibly, so the player feels they are keeping this creature with their own hands (vision-v2 §4).

## What to build

1. **Home = the vial.** The 3D vivarium fills the home screen with the player's current individual (stage, sex, traits,
   behaviour from the brain/API) and the vial state (food, humidity, mould, cleanliness, temperature). The frosted UI from
   W15 sits on top: today's needs, time of day, the next thing to do. Multiple vials (the colony) can be swiped.
2. **Food you mix goes into the vial.** Map the meal block-puzzle result to food-medium parameters (colour, moisture,
   yeast, nutrition) via the existing scoring; after the puzzle, animate the new medium being poured/placed and the larvae
   burrowing into it. Server stays the source of truth: extend the API (domain + DB, new Alembic migration after the
   current head) with a persisted vial state if needed, and spec it in `docs/specs/game-rules.md`.
3. **Training you do shows up in behaviour.** After a training session, the next time an odour is present in the vial the
   fly approaches/avoids according to the brain model (use the existing association/odour-choice endpoints). Show it as
   a short moment ("バナナの匂いに寄っていった"), not a number.
4. **Cleaning by hand.** Replace the abstract cleaning with wiping condensation/mould/grime off the glass with a finger
   (raycast on the glass, erase a mask). Score from coverage/time, same reward rules.
5. **Temperature/humidity dial.** A tactile dial overlay; the fly's pace and the condensation respond immediately.
6. **Pupation site.** The wandering larva climbs the glass; the player taps where it should stop; the pupa forms there.
7. **Eclosion day** (former 研究発表会): a cinematic in the vial — the adult emerges, wings unfold and harden, then its
   evaluation and title appear. Keep the existing reward logic.
8. **Neglect is visible.** Dry food, mould and sluggish behaviour appear when care is missed (from server state), so
   coming back matters.
9. Keep puzzles' rules and server-side scoring intact; only their framing and consequences change. Update the week E2E.
10. Performance: the 3D chunk loads only where used; low tier on weak phones; no layout jank on mobile.

## Done when

- API tests (targeted while developing, full once — the host CPU cools poorly), ruff, web lint/typecheck/test/build and the
  Playwright week E2E pass; new screenshots of home, meal→vial, cleaning, eclosion in `docs/media/v2/`.
- Many small atomic commits (API vial state, migration, each care mapping, each screen, cinematics, E2E, screenshots, docs).
