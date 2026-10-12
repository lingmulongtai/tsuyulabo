# Task W14-vivarium-3d — a photoreal 3D vivarium and fly, driven by the brain model

Branch: `feat/vivarium-3d`. Read `docs/specs/vision-v2.md` first: it is the source of truth and overrides older specs.

**You own only**: `apps/web/src/components/vivarium/**` (new), `apps/web/src/app/vivarium/**` (new preview route),
`apps/web/public/vivarium/**` (new assets), and the dependency lines in `apps/web/package.json` / `package-lock.json`.
Another agent (W15) is rewriting copy, design tokens and every other component in parallel — do not edit anything else.

## Goal

The owner wants the game to move from cute 2D art to **hyper-real macro photography in Three.js**. Build the hero of
the whole game: a glass culture vial seen through a macro lens, with a living *Drosophila melanogaster* inside at any of
its four stages. It must look like a photograph, move like a real animal, and run on a phone. Quality is the priority —
iterate on the look with screenshots until it is genuinely convincing, not "a 3D model of a fly".

## What to build

1. **Stack**: `three`, `@react-three/fiber`, `@react-three/drei`, `@react-three/postprocessing` (check versions that
   support React 19 / Next 16 and the repo's current Next version). Client-only (`dynamic(..., { ssr: false })`).
2. **Scene** (`<Vivarium stage behaviour environment quality />`):
   - Vial: real glass (transmission/refraction, thickness, IOR ≈1.5, subtle fingerprints/scratches roughness map,
     curved specular highlights), cotton/foam plug, condensation droplets on the inner wall (instanced, refractive),
     amount driven by humidity.
   - Food medium at the bottom: yellow cornmeal-agar with wet sheen, yeast speckles on the surface, larval tunnels;
     colour/moisture/yeast parameters exposed (W16 will drive them from the meal puzzle).
   - Optional environment props: mould patches and grime on the glass (parameters for W16's cleaning).
   - Lighting: warm amber key light, soft fill, rim light, an HDRI/environment for reflections (generate or use a small
     CC0 HDRI committed under `public/vivarium/` with its licence noted); soft shadows / contact shadows.
   - Camera: macro lens feel — narrow FOV, **shallow depth of field that keeps focus on the fly** (auto-focus follows it),
     orbit/pinch to look around and zoom within limits, gentle idle drift.
   - Post: depth of field, subtle bloom on highlights, SSAO/N8AO, slight vignette and film grain, filmic tone mapping
     (ACES/AgX), correct sRGB output.
3. **The fly, all stages** — procedural geometry and shaders (or CC0 assets if clearly licensed; note the source):
   - Adult: red compound eyes with visible hexagonal ommatidia when close, iridescent thin-film wings with veins,
     bristles (instanced hairs) on thorax/head, tan body with dark abdominal bands; male/female differences (sex combs,
     abdomen tip) and visible genetic traits from the API (white/yellow/curly/etc. per `docs/specs/genetics.md`).
   - Larva: translucent white with subsurface scattering, visible gut/trachea inside, black mouth hooks, segmented
     peristaltic crawling, burrowing into the medium.
   - Egg: small white ovals with two filaments on the medium surface. Pupa: amber case darkening over time on the glass.
4. **Behaviour from the brain**: an animation controller that takes the behaviour labels the game already gets from the
   brain decoder (inspect `apps/web/src/lib/api` and the brain viewer / adult detail code to find the actual labels:
   walk, stop, groom, feed, flee/escape, approach/avoid an odour, fly, …) and blends procedural locomotion
   (tripod gait for adults, peristalsis for larvae), grooming, feeding with proboscis extension, take-off and short
   flights inside the vial, approach/avoid towards an odour source. Never a fixed loop: seed variation per individual.
   Expose a small API (`setBehaviour`, `pointOfInterest`) so W16 can drive it.
5. **Quality tiers**: `high` (all post, shadows), `medium`, `low` (no DOF/SSAO, fewer hairs/droplets), chosen
   automatically from device/GPU and frame time, overridable. Target 60 fps on a mid-range phone at `medium`.
   No WebGL → a static rendered image fallback. Respect `prefers-reduced-motion` (slower, calmer motion).
6. **Preview route** `/vivarium`: full-screen scene with a minimal dev panel (stage, behaviour, sex, traits, humidity,
   food parameters, mould, quality) for review. No game data required; works in the public demo.
7. **Proof of quality**: Playwright screenshots (headless WebGL) of each stage at close and wide framing, light and dark
   system theme irrelevant (the scene is the scene), committed to `docs/media/v2/vivarium-*.webp`, plus a short
   `apps/web/src/components/vivarium/README.md` describing the techniques, parameters and performance budget measured.
   Look at your screenshots critically and fix what looks fake (plastic sheen, uniform colours, hard edges, wrong
   scale, flat lighting) before finishing.

## Done when

- `npm.cmd run lint`, `typecheck`, `test`, `build` pass in `apps/web`; vitest covers the behaviour controller and the
  quality-tier selection (pure logic).
- `/vivarium` renders all four stages and the behaviours; screenshots committed; bundle impact documented (keep the
  3D code in its own chunk, not loaded on other routes).
- Many small atomic commits (deps, scene shell, glass, medium, lighting, camera/DOF, post, each stage, wing shader,
  eye shader, hairs, each behaviour, tiers, fallback, preview route, screenshots, docs — each separate).
