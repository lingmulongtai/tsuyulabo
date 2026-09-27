# Tsuyu Labo brain engine

`tsuyu_brain` is a small CPU PyTorch LIF network for the game's adult flies.
It implements deterministic batched simulations, individual variation, dopamine
learning, and a trained behavior decoder. No database, web framework, external
service, or network access is needed at runtime.

## Run from the repository root

```powershell
.\.tools\uv.exe run pytest services/brain
.\.tools\uv.exe run pytest services/brain -m eval
.\.tools\uv.exe run ruff check services/brain
.\.tools\uv.exe run python -m tsuyu_brain.eval
```

The first command selects fast tests using the root pytest configuration.
Evaluation takes a few minutes and writes `eval-results/brain/report.json` and
`report.md` relative to the repository root (even from a different working directory).
Reports are generated artifacts, not source files. A failed criterion exits with status 1.

## Public facade

```python
from tsuyu_brain.api import (
    generate_individual,
    new_fly_state,
    apply_training,
    preference_index,
    predict_behavior,
    run_odor_choice,
)
from tsuyu_brain.learning import FlyState

params = generate_individual(["keen_nose", "glutton"], sex="f", seed=7)
state = new_fly_state(params)
for seed in range(3):
    state, association = apply_training(state, "banana", "reward", 1.0, seed)
pi = preference_index(state, "banana", seed=10, trials=20)
probabilities = predict_behavior(state, {"scenario": "liked_odor", "cue": "banana", "seed": 10})
counts = run_odor_choice(state, "banana", trials=20, seed=10)
restored = FlyState.from_bytes(state.to_bytes())
```

`strength` is in `[0, 1]`; valence is `reward` or `punish`. Cues are `banana`,
`apple_vinegar`, `yeast`, `grape`, and `blue_light`. `association` is the signed
post-training neural preference index. Training returns a new state; simulations
and choice trials do not change their input. The API accepts a scenario string,
`BehaviorContext`, or a dictionary with `scenario`, `cue`, `intensity`, and `seed`.
Intensity defaults to 1 and is limited to `[0, 5]`; the decoder is evaluated near 1.

Scenarios: `rest`, `walk`, `sugar`, `bitter`, `sugar+bitter`, `looming`, `light_left`,
`light_right`, `antenna_touch`, `liked_odor`, `disliked_odor`. The odor scenarios
present the specified cue to the **existing** state; their names do not train it or
force an output label. `walk` models increased tonic arousal; `rest` retains weak
spontaneous walking-neuron activity. Bitter and sugar+bitter are labeled rest.

Probabilities cover `rest`, `walk`, `turn_left`, `turn_right`, `feed`, `escape`,
`groom`, `approach`, and `avoid`. Choice trials use independent Poisson trials and
Bernoulli readout with probability `(PI + 1) / 2`; a small sample need not match
the population preference direction exactly.

## Simulation and state contracts

- Time is in milliseconds; rates are Hz; `dt=0.5`, `tau_m=20`, `tau_syn=5`,
  refractory period 2, rest/reset voltage 0, default threshold 1.
- `Circuit.weights[source, target]` contains signed current impulses. Input
  groups are clamped Poisson sources; the remaining cells are LIF populations.
  Stimulus values multiply the individual's input rate (default 180 Hz).
- `simulate` returns group rates `[batch, window]`, neuron rates `[batch, neuron]`,
  actual window durations, and optional raster `[time, batch, neuron]`. Durations
  must be positive multiples of 0.5 ms. The last window may be shorter.
- A local `torch.Generator` controls randomness. Identical inputs and seeds are
  reproducible within a PyTorch/platform version; cross-version bit identity is
  not promised. No inference operation changes the global random seed.
- Registry circuits are shared and must be treated as read-only. Tensor mutability
  remains a Python caller responsibility; use `with_weights` to make private edits.
- `BrainParams` holds 24 floats. Traits apply the exact shifts in game-rules §7
  plus small Gaussian individual noise. Sex is validated but has no invented
  physiological effect. Exclusive trait pairs, unknown traits, and duplicates fail.
- A toy fly stores only parameters and 200×2 KC→MBON weights. Versioned JSON bytes
  contain little-endian float16 weights encoded as base64 (under 4 KB). This is
  intentionally lossy at float16 precision. Runtime weights remain float32.
- Reward activates PAM and depresses active KC→MBON_av synapses; punishment
  activates PPL1 and depresses KC→MBON_ap. KC activity traces and DAN activity are
  measured in simulation, weights clip at zero, and PI uses simulated MBON rates.

## Neuron names and the real / model / game boundary

| Circuit | Named populations |
| --- | --- |
| `olfaction_mb` | ORN (8), PN (8), KC (200, six random PN partners each), APL, MBON_ap, MBON_av, PAM, PPL1; vision also drives 40 KCs |
| `feeding` | Gr64f sugar GRNs, Gr66a bitter GRNs, feeding interneurons, MN9 |
| `escape` | LPLC2, LC4, DNp01 |
| `steering` | left/right photoreceptors, DNa02_L/R, walking_DN |
| `grooming` | JO, aDN |

**Real:** cell-type names and broad pathway motifs motivate the circuits.
**Model:** `toy-v0` counts, weights, tuning, gains, signs, neuron replication, and
timing are synthetic, not a measured connectome or fitted fly physiology. The
direct negative Gr66a→MN9 edge summarizes bitter-mediated inhibition. MBON_ap/av
are functional output names. Sparse convergent sensory projections in steering
and grooming represent selective recruitment within a pooled DN population.
**Game:** traits, scenario labels, arousal, and binary choice readout are gameplay
abstractions. High decoder accuracy measures consistency with synthetic scenario
labels, not biological validity. This does not simulate a whole fly or establish
sentience or consciousness.

## Decoder and evaluation

The decoder sees eight output-neuron rates, never scenario IDs or stimulus labels.
Both multinomial logistic regression and a 16-hidden-unit tanh MLP use handwritten
logits/losses with torch autograd and Adam. Data defaults to 16 individuals × 11
scenarios × 4 trials (704 rows), varying traits, sex, intensity, cues, and seeds.
Train/test splits keep all trials from an individual together; normalization uses
training rows only. Both models must reach 85% held-out accuracy.

The control permutes **all entries, including zeros, within each projection and presynaptic sign**,
preserving groups, signs, and weight distributions. It reruns matched individuals
and trials through the frozen decoder, without retraining. Three fixed shuffle
seeds are reported with confusion matrices; an average drop of at least 10
percentage points makes the spec's qualitative "large drop" concrete. The initial
uniform projections were insensitive to this control; selective convergence is
needed for within-projection topology to affect these pooled output rates.

`decoder/weights/toy-v0.pt` is a ~4 KB MLP checkpoint, trained with dataset seed 123,
split seed 7, optimizer seed 11, and 400 epochs. Loading uses `weights_only=True`.
If absent, the same model trains on demand and is cached in memory. Offline
training temporarily uses one torch thread and restores the previous setting;
do not run training concurrently with application inference.

To regenerate explicitly:

```python
from tsuyu_brain.decoder.dataset import generate_dataset, split_dataset
from tsuyu_brain.decoder.model import train_decoder

train, _ = split_dataset(generate_dataset())
train_decoder(train, "mlp").save("services/brain/src/tsuyu_brain/decoder/weights/toy-v0.pt")
```

The evaluation also reports MN9 sugar activation/bitter suppression, looming
DNp01 activation, ±0.3 banana PI shifts after three training sessions, and the
right-turn fraction for 32 independent flies per trait group (one-sided Welch
test, p < 0.01). These are tests of the model's intended behavior.

## MaleCNS v1.0: measured subcircuits (experimental)

`load_circuit(name, version="malecns-v1.0")` loads the bundled measured extract.
**The default remains `toy-v0`.** Real topology does not by itself validate the LIF
model, the game stimuli, or the learned decoder. All six promotion gates must pass
before changing the default. The existing toy decoder checkpoint is unchanged;
MaleCNS evaluation trains its own models and never loads that checkpoint.

```python
from tsuyu_brain.connectome import load_circuit
from tsuyu_brain.learning import new_fly_state
from tsuyu_brain.params import default_params

circuit = load_circuit("escape", version="malecns-v1.0")
state = new_fly_state(default_params(), version="malecns-v1.0")
```

The measured state stores 200×20 KC→MBON magnitudes (ten approach and ten avoidance
MBONs); reconstruction restores the original presynaptic signs. It uses the same
learning rule and float16 serialization, with shape inferred from its version.
This experimental state is larger than the toy game's 4 KB budget. The public
game facade defaults to toy states and rejects MaleCNS behavior decoding until
a compatible decoder passes evaluation.

### Provenance and license

Source: [official MaleCNS downloads](https://male-cns.janelia.org/download/),
release `male-cns:v1.0`, synapse confidence cutoff 0.5.
The derived matrices and annotations retain [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Attribution: FlyEM / HHMI Janelia, University of Cambridge, MRC Laboratory of
Molecular Biology, and Google Research.

Berg, S., Beckett, I. R., Costa, M., et al. (2026).
*Sexual dimorphism in the complete Drosophila male central nervous system connectome.*
Cell 189, 5504–5526.e15. [doi:10.1016/j.cell.2026.08.015](https://doi.org/10.1016/j.cell.2026.08.015).
The transformations here select and sample neurons, omit boundary connections,
apply signs and scales, and pool outputs for a game. They are not an endorsed
physiological model from the dataset authors.

The inputs remain under git-ignored `data/raw/malecns-v1.0/`. The bundled
`src/tsuyu_brain/connectome/malecns_v1/manifest.json` records all three SHA-256
hashes, full Arrow schemas, rules, actual type counts, seed, scales, and TODOs.
Each circuit JSON records the ordered body IDs, real types, raw/consensus
transmitter calls, chosen sign source, groups, and projections. The manifest
hashes both NPZ and JSON artifacts; loading checks them.

| Input filename prefix | Rows | Relevant schema |
| --- | ---: | --- |
| `body-annotations-...` | 211,577 | `bodyId: int64`; `type`, `instance`, `somaSide`, `rootSide`, `synonyms`, `receptorType`: string |
| `body-neurotransmitters-...` | 1,835,518 | `body: int64`; `predicted_nt`, `consensus_nt`: string; prediction confidence: double |
| `connectome-weights-...` | 151,856,684 | `body_pre`, `body_post`, `weight`: int64 |

Arrow projects columns and filters 65,536-row batches with single-batch readahead.
The 1.1 GB weights file is scanned, never converted wholesale to pandas or a dense
matrix. Only retained small subgraphs become dense tensors at runtime. Compressed
CSR float32 preserves scaled counts exactly here; the entire bundle is below
0.8 MB, so lossy float16 matrix storage is unnecessary.

### Cell selection and aliases

| Circuit | Actual selection | Neurons |
| --- | --- | ---: |
| `olfaction_mb` | ORNs for DM1/2/3/4, VA2, VM2, DL1, DC2; matching uniglomerular ad/l/v/lv PNs; 200 seeded KCs; APL; MBONs below; reward PAMs; punishment PPL1s; 32 R8p photoreceptors | 987 |
| `feeding` | LB3b/c sugar and LB1a–d bitter GRNs; MN9; named feeding cells and measured two-hop intermediates | 113 |
| `escape` | exact LPLC2, LC4, DNp01 (giant fiber) types | 313 |
| `steering` | 64 R8p/y photoreceptors per root side; DNa02 per soma side; DNp09 walking neurons | 132 |
| `grooming` | JO-C/E/F/mz; DNg62 and DNge078; measured two-hop intermediates | 524 |

Sampling uses NumPy's seeded generator, seed 1729, after sorting body IDs. The
input order never determines selection. Both hemispheres are retained. The
manifest gives the exact body/type counts after unresolved transmitters are
excluded. No neurons or synapses are invented to fill gaps.

The supplied annotations have no Gr64f or Gr66a type/receptor labels. Searches of
type, instance, synonyms, receptorType, hemibrainType, and flywireType therefore
needed external receptor-mapping evidence. [Tastekin et al. (2026), Cell,
Fig. 2E](https://doi.org/10.1016/j.cell.2026.08.016) maps Gr64f-GAL4 to LB3b/c and
Gr33a-GAL4 bitter GRNs to LB1a–d. `Gr66a` remains the game's bitter-channel alias,
**not verified Gr66a expression per body**; this is an explicit TODO. Sugar SEL
neurons (GNG056/540/550) are interneurons and were not relabeled as GRNs.

Feeding seeds include GNG108/Roundup, GNG120/Roundtree, GNG175/Usnea,
ANXXX462a/Clavicle, DNge080/Rounddown, and DNg67/Fudog, using the annotations'
Shiu 2022 synonyms. Feeding and grooming each add at most 96 annotated bodies
on measured sensory→interneuron→output paths, ranked by the smaller of summed
incoming and outgoing counts, with body ID breaking ties. This topology rule
is fixed before calibration; it does not select on simulated behavior.

The annotations explicitly identify DNg62 as aDN1 and DNge078 as aDN2 (Hampel 2015).
The JO-C/E/F/mz selection follows the grooming pathway studied by
[Shiu et al. (2024), Nature](https://doi.org/10.1038/s41586-024-07763-9).
DNp09 is a walking output based on [Braun et al. (2024), Nature](https://doi.org/10.1038/s41586-024-07523-9).
The label `aDN` excludes unrelated AOTU103m synonyms and ADNM motor neurons.

### MBON valence mapping

`MBON_ap` and `MBON_av` are pooled behavioral readouts, not anatomical cell types.
Selection uses published functional valence, separately from synaptic polarity:

| Pool | MaleCNS types | Published compartment names |
| --- | --- | --- |
| approach | MBON11 | γ1pedc→α/β (MVP2) |
| approach | MBON12 | γ2α′1 |
| approach | MBON14 | α3 |
| avoidance | MBON01, MBON03, MBON04 | γ5β′2a, β′2mp, β′2mp bilateral |
| avoidance | MBON05, MBON06 | γ4→γ1γ2, β1→α |

The number/compartment mapping and activation assays come from
[Aso et al. (2014), eLife, Table 1 and Figs. 2–3](https://doi.org/10.7554/eLife.04580).
The approach roles of MBON11/14 and the opposing feedforward paths are also
illustrated in [Li et al. (2020), eLife, Figs. 40–41](https://elifesciences.org/articles/62576/figures).
Other MBON types are deliberately left unassigned rather than giving them an
unsupported valence. Pooling does not capture context-dependent functions.

PAM inputs use reward-associated PAM01/02/04/05/06/07/08/09/10/11/15; PPL1 inputs
use punishment-associated PPL101/103/106. These functional subsets follow
[Rubin and Aso (2024), eLife](https://elifesciences.org/articles/90523/figures);
PAM12–14 are not incorrectly treated as generic reward neurons.

### Signs and model boundaries

Signs first use the per-body `predicted_nt`; unsupported/unclear predictions fall
back to the supplied `consensus_nt`. Bodies still without a supported sign are
excluded. There is no confidence threshold beyond the release's predictions.
ACh is positive, GABA and glutamate negative. Treating glutamate as inhibitory is
a default fly-CNS modeling choice, **not a receptor-specific biological fact**.
Histamine is negative for the selected photoreceptors. Dopamine is represented
by positive current in this LIF approximation, while DAN firing also gates the
existing plasticity rule. This does not model dopamine receptor kinetics.

The raw classifier calls most KCs dopamine, while the dataset consensus calls
them acetylcholine. Both map to positive current here; raw predictions and the
disagreement are retained for review. ACh/GABA/Glu predictions are never flipped
to obtain a behavioral result. Functional pools may mix signs, so shuffled
controls permute weights and zeros within each projection **and source-sign
stratum**, preserving every neuron's output sign.

**Real:** selected body identities and all retained synapse counts.
**Model:** omitted boundary/relay cells, sign assumptions, LIF dynamics, current
scales, Poisson rates, pooled outputs, and dopamine learning.
**Game:** fruit labels, glomerular encoding, traits, tonic walking drive, and
scenario/decoder labels. Banana/DM1, vinegar/DM2, yeast/DM3, and grape/DM4 are game
channel assignments, not validated odor-response maps. The R8→visual-KC route
and multi-stage photoreceptor→DNa02 route are incomplete; no direct synthetic
edge replaces them. A missing population remains an empty, silent group with a
manifest TODO. A test of implementation correctness is not a passed promotion gate.

### Reproduce ingestion and evaluation

All commands run from the repository root. Arrow/pandas are in the `ingest`
optional extra of `tsuyu-brain`; runtime installation does not require them.

```powershell
.\.tools\uv.exe sync --all-packages --extra ingest
.\.tools\uv.exe run --all-packages --extra ingest python services/brain/scripts/ingest_malecns.py --inspect
.\.tools\uv.exe run --all-packages --extra ingest python services/brain/scripts/ingest_malecns.py --seed 1729 --scale feeding=0.0625 --scale escape=0.000244140625 --scale olfaction_mb=0.1875 --scale steering=0.03125 --scale grooming=0.0078125
.\.tools\uv.exe run python services/brain/scripts/calibrate_malecns.py
.\.tools\uv.exe run python -m tsuyu_brain.eval --version malecns-v1.0
.\.tools\uv.exe run pytest services/brain
.\.tools\uv.exe run pytest services/brain -m eval
.\.tools\uv.exe run ruff check services/brain
```

Ingestion defaults to scale 1/32 for experimentation; the explicit flags above
reproduce the bundled calibration. All input rates remain 180 Hz. Only one global
scale per circuit was tuned; thresholds, learning rate, individual traits, and
edge ratios were unchanged. The sweep uses seed 19; evaluation uses independent
fixed seeds 71/81 plus its original individual/decoder seeds. Feeding uses the
first tested scale producing sugar activation and bitter suppression; escape and
grooming use their lowest tested active scale. Olfaction uses the lowest tested
scale yielding MBON activity. Steering retains 1/32 because scaling cannot
supply the missing visual pathway.

The evaluation writes `eval-results/brain/report-malecns.md` and `.json`; it exits
1 when any gate fails. Toy reports retain their original filenames. Committed
copies and the complete calibration sweep are in `services/brain/reports/`.
Unit tests check the artifacts and runtime contracts. Slow tests check the
measured responses and report known gate failures explicitly. With raw files and
the ingest extra present, an additional slow audit verifies source SHA-256s and
that every stored edge is exactly the original count times its sign and scale.

### Evaluation result for the bundled extract

Full evaluation on PyTorch 2.14.0: **3/6 gates pass; do not promote the default**.
The full MaleCNS decoder evaluation took about 17 minutes on this Windows host;
it reruns all 16 individuals for each of three shuffle controls.

| Gate | Result | Measurement |
| --- | --- | --- |
| sugar → MN9 | pass | 2.917 Hz versus 0 at rest |
| looming → DNp01 | pass | 25.417 Hz versus 0 at rest |
| bitter suppression | pass | sugar+bitter 1.146 Hz, 39.3% of sugar alone |
| three-session learning | fail | baseline PI +1; reward ΔPI 0; punishment ΔPI −1 |
| right-turner trait | fail | both populations have zero right-turn fraction; p undefined |
| decoder / shuffled control | fail | logistic and MLP 46.59%; shuffled MLP 40.91% for all three seeds; drop 5.68 percentage points |

The reward criterion requires +0.3 and has no headroom from this extract's
baseline PI +1. The trait criterion lacks a complete sensory pathway. Decoder
accuracy is below 85% and the shuffled drop below 10 percentage points. These
failures are not waived by the passing implementation tests; `toy-v0` remains
the default. Missing visual relays, functional annotation uncertainty, and the
response imbalance require further scientific work, not per-edge tuning here.

Validation: 60 fast tests passed (26.7 s), 8 slow tests passed (236 s), Ruff lint
and format checks passed, and a built wheel contains all 11 circuit assets.
The slow suite verifies both measured responses and honest failure reporting;
it does not assert that the unvalidated extract passes all promotion gates.
See [full Markdown report](reports/report-malecns.md),
[JSON measurements and confusion matrices](reports/report-malecns.json), and
[39-condition scale sweep](reports/calibration-malecns.json).
