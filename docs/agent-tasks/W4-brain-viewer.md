# Task W4-brain-viewer — neural activity endpoint + brain viewer screen

Branch: `feat/brain-viewer`. Work in `services/brain/` (façade addition), `services/api/` (endpoint) and
`apps/web/src/app/adults/[id]/brain/` + `apps/web/src/components/brain/` (new).

The plan (企画書 §11, §13) mentions a 脳ビューア: show the player what happens inside Tsuyu's brain. Build a first
version:

1. **Brain façade**: `tsuyu_brain.api.activity(state, scenario, seed, windows=20) -> {groups: [{name, kind:
   "sensory"|"inter"|"output"|"modulatory", circuit, rates: [hz per window]}], edges: [{pre_group, post_group,
   weight_sum, sign}], scenario, duration_ms}` — group-level rates over time for one scenario (the behaviour
   scenarios already defined: sugar, bitter, looming, light_left/right, antenna_touch, liked_odor, disliked_odor,
   rest). Group-level only (dozens of nodes), cheap (< 200 ms), runs on a copy.
2. **API**: `GET /v1/flies/{id}/brain/activity?scenario=sugar` (adult id or the current week's larva), cached per
   (fly state version, scenario). Add it to OpenAPI and re-export the schema to `apps/web/src/lib/api/openapi.json`.
3. **Web**: `/adults/[id]/brain` — a node-link diagram (SVG, no new dependencies): sensory groups on the left,
   interneurons in the middle, outputs (MN9, DNp01, DNa02 L/R, MBONs) on the right, DANs as a modulatory row.
   Nodes glow by firing rate over time (play/pause scrubber through the windows), edges drawn by sign (excitatory /
   inhibitory colour) and weight. A scenario picker (「砂糖をあげる」「影を近づける」「バナナの匂い」…). Show real neuron
   names with a 本物 badge and the model caveat with a モデル badge. Match the existing design tokens and
   components (`src/components/ui/*`, `TruthBadge`). Add a link to it from `/adults/[id]`.
4. Tests: brain façade unit test (shape, determinism, no mutation), API router test, vitest for any layout helper.

## Done when

`uv run pytest`, web lint/typecheck/test/build pass. Atomic commit plan entries.
