# Task W1-brain — brain engine (`services/brain`)

Branch: `feat/brain-engine`. Work only in `services/brain/` (plus a HANDOFF.md log entry at the end).

Read first: `AGENTS.md`, `docs/specs/brain.md` (the spec you implement), `docs/specs/game-rules.md` §7 (traits table).

## Build

Package `tsuyu_brain` (src layout already exists; dependencies torch/numpy/scipy already declared — avoid adding new ones).

1. `neuron.py` — LIF population with current-based synapses, refractory period, dt=0.5 ms, batch dimension
   (shape `[batch, n]`). Poisson input generator. Deterministic with `torch.Generator` seeds.
2. `circuit.py` — `Circuit` dataclass: named neuron groups (name → index slice), weight matrix (dense or
   sparse), excitatory/inhibitory signs, input groups, output groups. `simulate(circuit, stimulus, params,
   duration_ms, batch, seed) -> SimResult` (spike raster optional, rates per group per window).
3. `connectome/toy_v0.py` — deterministic synthetic circuits named after real neurons, per the spec table:
   `olfaction_mb` (ORN→PN→KC(200)→APL, MBON_ap / MBON_av, DAN PAM / PPL1; include visual KCs for
   `blue_light`), `feeding` (Gr64f sugar GRN, Gr66a bitter GRN, MN9), `escape` (LPLC2, LC4, DNp01),
   `steering` (left/right photoreceptors, DNa02 L/R, walking DNs with spontaneous firing), `grooming`
   (JO mechanosensory → aDN). Version string `toy-v0`. A registry `load_circuit(name, version="toy-v0")`.
4. `params.py` — `BrainParams` (per-individual gains/thresholds/asymmetry, a few dozen floats), JSON
   (de)serialisable, `default_params()`.
5. `individuality.py` — `generate_individual(traits, sex, seed) -> BrainParams` with the trait effects from
   game-rules.md §7 plus small Gaussian noise. Mutually exclusive traits must raise if combined.
6. `learning.py` — mushroom-body dopamine rule. `FlyState` = params + learned KC→MBON weights (compact,
   serialisable to bytes, e.g. float16 base64; target < 4 KB). `new_fly_state(params)`,
   `apply_training(state, cue, valence, strength, seed) -> (new_state, association_value)`,
   `preference_index(state, cue, seed, trials) -> float` in [-1, 1]. Cues: banana, apple_vinegar, yeast,
   grape, blue_light. Valence: reward (PAM → depress KC→MBON_av) / punish (PPL1 → depress KC→MBON_ap).
7. `behavior.py` — scenarios (rest, sugar, bitter, sugar+bitter, looming, light_left, light_right,
   antenna_touch, liked_odor, disliked_odor) → feature vector from output neurons.
8. `decoder/` — dataset generation from simulated scenarios with individual variation; hand-written
   multinomial logistic regression (torch autograd, no sklearn) and a small MLP; train/eval split;
   accuracy + confusion matrix; "shuffled wiring" control (permute weights within each projection).
   Save trained weights to `services/brain/src/tsuyu_brain/decoder/weights/toy-v0.pt` only if small
   (< 200 KB); otherwise train on demand with a fixed seed and cache.
9. `api.py` — the small façade the game API will call:
   `generate_individual`, `new_fly_state`, `apply_training`, `preference_index`,
   `predict_behavior(state, context) -> {label: prob}`, `run_odor_choice(state, cue, trials, seed) ->
   {toward: int, away: int}` (for Shiori experiments on a copy; must not mutate the input state).
10. `eval.py` — `python -m tsuyu_brain.eval` runs the spec's evaluation table and writes
    `eval-results/brain/report.json` and `report.md` (paths relative to repo root, create dirs).
11. `scripts/ingest_malecns.py` — skeleton that documents how to turn MaleCNS v1.0 (CC-BY) exports into
    per-circuit `.npz` matrices with the same `Circuit` interface. Do NOT download anything; just the
    code path with clear TODOs and a README section with data source and citation.
12. `services/brain/README.md` — what it is, how to run tests/eval, the neuron names and the real/model/game
    boundary.

## Tests (pytest, `services/brain/tests/`)

Fast unit tests (< 30 s total): LIF dynamics (threshold, reset, refractory), determinism with seeds,
circuit shapes, each spec sanity check at small batch (sugar→MN9, looming→DNp01, bitter suppresses MN9),
learning changes PI in the right direction, state serialisation round trip and size, trait exclusivity,
run_odor_choice does not mutate state. Heavier statistical checks (trait effect significance, decoder
accuracy ≥ 85%, shuffled control) go under `@pytest.mark.eval`.

## Done when

- `uv run pytest services/brain` passes, `uv run pytest services/brain -m eval` passes,
  `uv run ruff check services/brain` is clean.
- `uv run python -m tsuyu_brain.eval` writes the report.
- Many atomic commits (one per module + its tests, fixes separately). Final entry in docs/HANDOFF.md Log.
