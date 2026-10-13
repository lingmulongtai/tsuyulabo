# Vivarium (W14)

An isolated, client-rendered macro habitat. Open `/vivarium`; expand 「飼育びんの設定」
to review the four stages, decoder actions, expressed traits, habitat and quality.
No game account, API, brain service, remote texture service or model download is required.

## W16 integration

Import **only** `Vivarium.tsx` from a client component. It uses `next/dynamic` with
`ssr: false`; importing the entry does not eagerly import Three.js. Give its parent
an explicit height. React 19 refs are supported directly.

```tsx
import { useRef } from "react";
import { Vivarium, type VivariumHandle } from "@/components/vivarium/Vivarium";

function HabitatPreview() {
  const view = useRef<VivariumHandle>(null);
  const placeOdour = () => {
    view.current?.pointOfInterest([0.65, -1.08, -0.2]);
    view.current?.setBehaviour("approach");
  };
  return <div style={{ height: "70dvh" }}>
  <Vivarium
    ref={view}
    stage="adult"
    behaviour="walk"
    sex="f"
    traits={["white", "curly"]}
    seed="individual-id"
    quality="auto"
    environment={{
      humidity: 0.7,
      food: { color: "#bda45c", moisture: 0.7, yeast: 0.4 },
      mould: 0.1,
      grime: 0.2,
      pupaAge: 0.4,
    }}
  />
    <button onClick={placeOdour}>匂いを置く</button>
  </div>;
}
```

- `stage` accepts the API's `egg`, `larva1`, `larva2`, `larva3`, `wandering`, `pupa`,
  `adult`, plus the preview alias `larva`. Instars differ in size.
- Decoder labels are `rest`, `walk`, `turn_left`, `turn_right`, `feed`, `escape`,
  `groom`, `approach`, `avoid`. `fly` and `burrow` are explicit motor previews;
  `stop` and `flee` alias resting/escape behavior. This component does not fabricate
  brain decisions or sample the API's probability map: pass the selected label.
- Use **expressed `phenotypes`**, never hidden carrier alleles or only `strain`.
  `white`, `yellow`, `ebony`, `curly`, `vestigial` combine. The visual-only rule for
  simultaneous yellow/ebony is ebony precedence; simultaneous curly/vestigial keeps
  both shortening and curl. The server still owns inheritance. Vestigial adults
  escape on foot. Male abdomen pigmentation/tip and foreleg sex combs differ.
- Environmental scalars are normalized **0–1**, clamped with finite defaults.
  `pupaAge` darkens the case. Food color is a CSS/Three color; moisture changes its
  sheen, yeast changes surface colonies, mould adds patches, grime increases haze.
- Coordinates are illustrative world units, **not measured millimetres**. Y is up;
  food surface is `-1.075`, inner vial radius about `1.065`. The organism is kept
  inside using a radius budget that includes wings. The source may be outside its
  reachable footprint. `pointOfInterest` supplies the odour/light position.
- Props apply when they change. Imperative commands take effect immediately; only
  calls made before mounting are queued, consumed once. Prop changes subsequently
  take precedence. Changing `seed` or `stage` resets motor state.
- `framing="close"` tracks the individual, with optical magnification adjusted for
  eggs/pupae. Drag rotates, pinch/wheel zooms within bounds. `paused` stops motor
  motion and idle drift while still allowing inspection and habitat edits.
- Reduced-motion slows motor timing to 35% and disables idle drift. Hidden documents
  stop the continuous render loop. WebGL absence, context loss and render errors
  show a stage-specific static render; reload to retry a lost context.

## Rendering

The vial uses a closed lathed wall/base/lip profile, physical transmission, IOR 1.48,
thin refraction and a procedural scratch/fingerprint roughness map. A rounded foam
plug has pore texture and instanced fibres. Refractive water droplets (IOR 1.333)
increase nonlinearly with humidity. Native Three transmission and alpha blending
are a deliberate approximation for nested transparent surfaces; this is not a
path-traced multi-layer optical simulation.

Cornmeal uses generated albedo/bump texture, recessed tunnel patterns, wet clearcoat,
and instanced yeast/mould. Adults have a shaped, marked thorax; banded, tapered
abdomen; compound-eye hexagonal bump/albedo; instanced bristles and articulated
legs. Wing membranes use physical thin-film interference with spatially varying
180–620 nm thickness and separate veins. Larvae have a continuous deforming cuticle,
internal gut/tracheal detail, volume absorption and an inexpensive scattering-rim
approximation (not full subsurface transport). Eggs have paired respiratory filaments;
pupae have shallow case segmentation and age-dependent pigmentation.

The motor controller blends actions and bounds time steps after suspension. A stable
individual seed changes steering, stride cadence, breathing phase and flight-burst
duration. Adults use alternating tripod groups, moving forelegs for grooming and an
extending proboscis for feeding. Larval contractions travel down the continuous skin;
feeding/burrowing lowers it into the medium. No React state is updated every frame.

Warm key, cool fill, rim and an original 256×128 RGBE studio environment supply light.
ACES tone mapping and sRGB output are explicit. High adds SSAO, autofocus DOF, subtle
bloom, vignette and grain; medium drops SSAO and lowers post/DPR cost. The HDR is CC0;
see [`public/vivarium/LICENSE.md`](../../../public/vivarium/LICENSE.md).
Regenerate it from the repository root with:

```powershell
node apps/web/src/components/vivarium/generate-environment.mjs
```

## Budgets and measurements

| Tier | Max DPR | Hairs | Maximum droplets at 100% humidity | Shadows | Post |
| --- | ---: | ---: | ---: | --- | --- |
| high | 1.75 | 420 | 110 | 2048 map | DOF, SSAO, bloom, grain, vignette |
| medium | 1.25 | 180 | 48 | 1024 map | DOF, bloom, grain, vignette |
| low | 1 | 65 | 16 | off | off |

Auto starts conservatively from hardware concurrency, reported memory, coarse pointer
and software-renderer detection. After warmup, sustained <48 fps over three seconds
lowers one tier; it never oscillates upward. Explicit overrides remain fixed. Large
resume gaps do not count against quality. Slow 300 ms frames do count.

The isolated W14 preview's production browser network inspection found about **1.12 MiB additional JavaScript,
312 KiB gzip**, across three route/renderer chunks. The large renderer chunk alone is
about **1.09 MiB / 303 KiB gzip**. The home route loaded none of those renderer bytes.
That was before W16 added the live home vial. The local HDR is 128 KiB; all eight
1400×1000 review WebPs total about 268 KiB.
These numbers include the Three/Fiber/Drei/postprocessing code, not the shared Next
runtime. No additional dependency versions in the original lockfile were upgraded.

Target: 60 fps at medium on a mid-range phone. **That hardware acceptance remains
unverified.** The headless SwiftShader software renderer used for repeatable screenshots
is not a proxy for a phone GPU. Measurements and limitations from the final run are
recorded below; do not present them as device acceptance or as photographic ground truth.

2026-10-12, production Next build, Chromium 153 headless, Windows, ANGLE Vulkan
SwiftShader, 390×844 CSS pixels, adult walking, no reduced-motion preference,
60 `requestAnimationFrame` intervals after 15 warmup intervals:

| Tier | Mean fps | p95 frame time | Draw calls including passes | Triangles including passes |
| --- | ---: | ---: | ---: | ---: |
| low | 2.79 | 683 ms | 56 | 111,620 |
| medium | 1.83 | 1,183 ms | 89 | 130,300 |
| high | 0.71 | 2,683 ms | 124 | 208,356 |

This software-only run is very slow; it confirms the relative tier cost, not the
60 fps target. Medium's current scene budget is under 100 total draw calls and
150k triangles including passes. Physical Android/iOS GPU profiling and visual
acceptance of the requested photographic realism remain open. These are procedural
anatomical approximations, not scanned specimens or a fully validated optical model.

## Verification and reproducibility

From `apps/web`: `npm.cmd run lint`, `npm.cmd run typecheck`, `npm.cmd run test`,
`npm.cmd run build`. The suite includes controller trajectories, action blending,
stage normalization, reduced motion, phenotype flight capability and sustained
frame-time quality selection. Final result: **274 tests across 28 files passed**;
lint, typecheck and production build passed. Browser checks passed for all nine
decoder actions plus flight, imperative/controlled precedence, pause during habitat
editing, no horizontal overflow at 390px, context loss, and WebGL disabled. A paused
pupal capture had exactly zero mean channel difference between light/dark system themes.

To reproduce screenshots and browser checks from the repository root:

```powershell
$env:PLAYWRIGHT_BROWSERS_PATH = "$PWD/.tools/browsers"
npx.cmd playwright install chromium
npm.cmd run build -w apps/web
npm.cmd run start -w apps/web -- --port 3015
# In another terminal, with the same PLAYWRIGHT_BROWSERS_PATH:
$env:VIVARIUM_URL = "http://127.0.0.1:3015"
node apps/web/src/components/vivarium/capture.mjs
```

The capture runner writes `docs/media/v2/vivarium-{stage}-{wide|close}.webp` and
four fallback assets, compares light/dark system themes, checks a 390px viewport,
all decoder actions, imperative/controlled precedence, pause, WebGL absence/context
loss, and samples 60 frames per quality tier after warmup. Its machine-readable
report is `.codex-runs/vivarium-report.json` (ignored). To repeat only browser checks,
set `VIVARIUM_SKIP_CAPTURES=1`. Do not rebuild `.next` while testing a running
production server; restart it after a build.

Visual iteration corrected glossy resin-like eyes, excessive pupal ridges, wire-like
food tracks, intersecting transparent larval segments and mobile framing. The
committed images are actual procedural WebGL renders, not reference photographs.
An owner review of the macro realism and physical-phone performance remains necessary.

## W16: the live rearing vial

Home mounts `ColonyVivarium` only after there is an active individual or an owned adult.
It renders one lazy Three scene at a time; the swipe strip changes the selected vial and
unmounts the old canvas. Camera orbit gestures and colony swipe gestures have separate
surfaces. Needs, available care, time of day and pause controls remain in glass panels.
The original cosmetic inventory remains under 「飼育棚の飾り」.

`CareVial` uses the same current-week ID, API stage and persisted `vial` as home. Meal
submissions return their verified medium; `CareConsequence` pours it into the substrate
and drives larval feeding. Accepted care results sit beside the vial rather than covering
it with a modal, so the pour and the learned odour choice remain visible and interactive.
A rejected submission cannot show a saved care consequence.
Temperature uses a glass dial overlay and the existing swinging-needle score;
touch/release or the stop button
freezes it. Humidity is a range dial. Preview pace/condensation change before submission;
the server saves them only on accepted care. Pupation taps select the nearest of the
three public site heights; confirmation still submits the existing option ID.

`GlassCare` raycasts the fixed-camera front half of the cylinder into a canvas texture.
Stamps erase its alpha mask. `wiping.ts` previews the same 18×12 cell coverage as Python;
the API validates the timestamps/coordinates and applies the existing cleaning rewards.
The disclosure 「静止画・キーボードで拭く」 sends the same stamps when WebGL is unavailable.
This keeps a usable fallback without pretending the static image reacts in 3D.

`OdourMoment` uses the existing one-trial odour-choice job on the owned brain snapshot.
Its measured toward/away outcome drives an eight-second approach/avoid moment; a tie
rests. Hidden documents and the home pause control preserve the remaining observation
time. Each new job starts a fresh moment even if the outcome is the same. Training waits
for a queued learning job before enabling observation. No association
value is converted into a made-up decision. Home's baseline is the decoder's finite
maximum; it refreshes every 30 seconds only while visible and unpaused.

Eclosion uses the server's saved vial and adult phenotypes. The case opens, the adult
emerges inward from the chosen site, its wings expand and harden, then evaluation/title appear.
Pause, visibility suspension, reduced motion and skip are supported. Rewards and adult
rolls remain in the existing API transaction. Environmental decay is documented in
`docs/specs/game-rules.md`; these visual scalars do not introduce new growth/reward rules.

Run the updated `week.spec.ts` and `vial-accessibility.spec.ts` against the real API.
The week runner saves actual home, meal, wiping and eclosion renders to
`docs/media/v2/integrate-*.webp`. Set `E2E_MEDIA_DIR` to override the destination and
`E2E_SOFTWARE_WEBGL=1` for reproducible software WebGL. The software renderer is very
slow; it is not physical-phone performance acceptance. Profile Android/iOS on device
before claiming the 60 fps target or absence of device-level frame drops.

### Run W16 on Windows

Use three terminals at the repository root. In the API terminal, warm the real brain
import before announcing server readiness; on a cold Windows host the first lazy import
can exceed the client's 12-second request timeout. This uses the real engine, not a test
adapter. Limit its CPU threads to keep the host cool.

```powershell
New-Item -ItemType Directory -Path .codex-runs -Force | Out-Null
$env:UV_CACHE_DIR = "$PWD/.uv/cache"
$env:DATABASE_URL = "sqlite+aiosqlite:///./.codex-runs/game.db"
$env:TSUYU_DEV_TOOLS = "true"
$env:RATE_LIMITS_ENABLED = "false"
$env:CORS_ORIGINS = '["http://127.0.0.1:3116"]'
$env:OMP_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
$env:OPENBLAS_NUM_THREADS = "1"
.\.tools\uv.exe run alembic -c services/api/alembic.ini upgrade head
.\.tools\uv.exe run python -c "import tsuyu_brain.api; import uvicorn; uvicorn.run('tsuyulabo_api.main:app', host='127.0.0.1', port=8116)"
```

In the web terminal:

```powershell
$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:8116"
$env:NEXT_PUBLIC_DEV_TOOLS = "1"
npm.cmd run build -w apps/web
npm.cmd run start -w apps/web -- --port 3116 --hostname 127.0.0.1
```

In the test terminal:

```powershell
$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:8116"
$env:E2E_BASE_URL = "http://127.0.0.1:3116"
$env:PLAYWRIGHT_BROWSERS_PATH = "$PWD/.tools/browsers"
$env:E2E_SOFTWARE_WEBGL = "1"
npm.cmd run test:e2e -w apps/web -- week.spec.ts vial-accessibility.spec.ts
```

The API defaults to inline brain jobs for this local run. Queue-mode acceptance needs
the configured Redis and real worker. The capture helper writes WebP review images,
not game assets.

### W16 verification (2026-10-13)

- API suite: 486 passed, 1 skipped, 2 excluded eval tests; full run performed once.
- Repository-wide ruff lint and format check passed (484 Python files).
- Web lint, typecheck and production build passed; 290 unit tests and 25 E2E-helper
  tests passed.
- Real-API Chromium week and WebGL-disabled phone/keyboard/colony tests both passed
  in the final run (14.9 minutes). Phone checks use a 390×844 browser viewport.
- SQLite migration round trip reached `0013`, downgraded to `0012`, and returned to
  `0013`; the non-null JSON vial column and default were inspected. PostgreSQL was
  not exercised by this local check.
- A production browser requested no Three renderer chunk on `/settings` or the
  empty home before receiving an egg. The week test required real ready WebGL
  canvases on home, care and eclosion; it also checked single-canvas colony rendering.
- The four `integrate-*.webp` images are actual renders from that week run and were
  visually inspected. Android/iOS hardware performance and realism acceptance
  remain open; SwiftShader cannot validate the 60 fps phone target.
