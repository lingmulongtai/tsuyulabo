# Task W18-realism-pass — make the vivarium actually look like a macro photograph

Branch: `feat/realism-pass`. Read `docs/specs/vision-v2.md` §3 (source of truth) and
`apps/web/src/components/vivarium/README.md`. Work mainly in `apps/web/src/components/vivarium/**`; keep its public API
stable for the screens W16 built on it (adapt call sites minimally if a change is unavoidable).

## Review of the current render (commander, 2026-10-12, `/vivarium` on a phone viewport)

It reads as "a 3D model", not "a photo". Concretely:

1. **Scale is wrong.** The adult is about a third of the vial's diameter. A real *D. melanogaster* is ~2.5 mm long; a
   standard vial is ~25 mm across and ~95 mm tall. The fly must be small in the wide shot — the macro camera's job is to
   get close. Build the scene in real millimetres and derive camera, DOF and light falloff from that.
2. **The food is a flat yellow cylinder.** It needs a meniscus against the glass, an uneven wet surface with specular
   breakup, yeast granules, darker moist patches, larval tunnels/pits, slight translucency at the edges, and it should
   fill the bottom ~20 mm of the vial.
3. **The fly looks like a toy.** Fix proportions (head ~ thorax width, eyes ~ half the head), real leg thickness and joint
   angles, wings folded flat over the abdomen at rest and nearly transparent with thin-film colour only at grazing
   angles, bristles readable at close range, no uniform plastic sheen — use layered roughness and colour variation.
4. **Glass and plug are flat.** The plug should be a dense foam/cotton with fibrous texture; the glass needs thickness
   at the rim, refraction of the background and of the food, faint smudges, and condensation clusters near the top.
5. **Background and light are flat.** Add a softly blurred environment (bench, warm lamp bokeh, cool window light),
   a stronger warm key with falloff, and let the DOF actually blur the far wall and background.
6. **Overlay text collides with the plug.** Compose the default framing so the title sits over empty background, and
   keep UI clear of the subject.

## What to do

- Fix all six items. Compare against real macro photographs of *Drosophila* culture vials (describe the references you
  used in the README, do not commit copyrighted images).
- Close-up framing must hold up: eyes' facets, wing veins, leg hairs.
- Keep 60 fps at `medium` on a mid phone; re-measure and document.
- Re-capture `docs/media/v2/vivarium-*.webp` (wide and close for each stage) and put before/after pairs in the README.

## Done when

- web lint/typecheck/test/build pass; screenshots updated; many small atomic commits (scale, medium, fly proportions,
  wing shader, materials, plug, glass, environment, light, framing, perf, screenshots, docs — each separate).
