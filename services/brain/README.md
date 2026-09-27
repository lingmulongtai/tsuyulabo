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
Evaluation defaults to MaleCNS and writes `eval-results/brain/report-malecns.json`
and `report-malecns.md` relative to the repository root. Explicit `--version toy-v0`
writes `report.json` and `report.md` instead (even from a different working directory). The measured
version with three complete shuffled simulations can take tens of minutes on CPU.
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

The toy decoder sees eight output-neuron mean rates. MaleCNS retains those output
windows and signed contrasts, then appends separate anatomical output readouts
(404 features total); neither decoder sees scenario IDs or stimulus labels.
Both multinomial logistic regression and a 16-hidden-unit tanh MLP use handwritten
logits/losses with torch autograd and Adam. Data defaults to 16 individuals × 11
scenarios × 4 trials (704 rows), varying traits, sex, intensity, cues, and seeds.
Train/test splits keep all trials from an individual together; normalization uses
training rows only. Both models must reach 85% held-out accuracy.
Selection uses an inner grouped development split (nine fit individuals and three
validation individuals); final models refit on all twelve training individuals.
Reports include exact IDs, seeds, validation confusion matrices, and an empirical
accuracy ceiling from conflicting labels on identical feature vectors.

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

train, _ = split_dataset(generate_dataset(version="toy-v0"))
train_decoder(train, "mlp").save("services/brain/src/tsuyu_brain/decoder/weights/toy-v0.pt")
```

The evaluation also reports MN9 sugar activation/bitter suppression, looming
DNp01 activation, ±0.3 banana PI shifts after three training sessions, and the
right-turn fraction for 32 independent flies per trait group (one-sided Welch
test, p < 0.01). These are tests of the model's intended behavior.

## MaleCNS v1.0: measured subcircuits (default)

`load_circuit(name, version="malecns-v1.0")` loads the bundled measured extract.
**The default is now `malecns-v1.0`: all six promotion gates pass.** Real topology
does not by itself validate the LIF model or game stimuli. The bundled measured
MLP checkpoint uses the same twelve training individuals as the passing report.
Explicit `toy-v0` circuits and stored toy states remain supported through their
unchanged checkpoint. Checkpoint version and exact feature ordering are verified
on load; a toy checkpoint cannot be used for a measured state.

```python
from tsuyu_brain.connectome import load_circuit
from tsuyu_brain.learning import new_fly_state
from tsuyu_brain.params import default_params

circuit = load_circuit("escape", version="malecns-v1.0")
state = new_fly_state(default_params(), version="malecns-v1.0")
```

The measured state holds 200×20 KC→MBON magnitudes (ten approach and ten avoidance
MBONs); reconstruction restores the original presynaptic signs. It uses the same
learning rule and float16 quantization, with shape inferred from its version.
To retain the application's compact-state contract, measured serialization XORs
the float16 bytes with the versioned initial weights and compresses the delta
with zlib. A SHA-256 prevents decoding against a different KC-MBON baseline.
Decoded weights exactly match the dense float16 representation, with no training
replay. The trained/eclosed API regression uses 1,169 bytes (below 3 KB); dense legacy toy
and measured payloads remain readable. Changing the baseline requires retaining
its version or an explicit migration; a checksum mismatch raises an error. The public game facade
creates measured states by default and selects the decoder from the persisted
state version. The activity viewer retains its 23 public display groups while
simulating the full measured circuits; additional output types are used by the
decoder but are not added to the existing viewer palette.

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
CSR float32 stores normalized weights; the entire bundle remains below 2 MB.
The source audit reconstructs each weight from raw counts and recorded factors.
JSON artifacts and reports use LF, so their committed bytes match manifest hashes.

### Cell selection and aliases

| Circuit | Actual selection | Neurons |
| --- | --- | ---: |
| `olfaction_mb` | Same sensory inputs, 200 KCs, APL and DANs; all exact numbered MBON types present in the release | 1054 |
| `feeding` | Same GRNs and MN9; MN6, MN11D/V, resolved MN12D; existing and additional measured two-hop intermediates | 173 |
| `escape` | exact LPLC2, LC4, DNp01 (giant fiber) types | 313 |
| `steering` | Same sensory inputs, DNa02, DNp09 and 192 visual relays; DNa01, DNb05/06 and DNg13 per soma side | 332 |
| `grooming` | Same JO and aDN populations; DNg11 and DNg12_a-h; existing and additional two-hop intermediates | 668 |

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
Shiu 2022 synonyms. Feeding and grooming retain their original bridges, then each add at most 96
annotated bodies on measured sensory->interneuron->new-output paths, ranked by
the smaller of summed incoming and outgoing counts, with body ID breaking ties.
The new pass adds 51 feeding and 96 grooming relay bodies. This topology rule
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
Other exact numbered MBON types are retained as separate anatomical output
readouts, without assigning an unsupported valence or adding a plasticity rule.
The original valence pools and 200×20 learned state remain intact. Pooling does
not capture context-dependent functions.

PAM inputs use reward-associated PAM01/02/04/05/06/07/08/09/10/11/15; PPL1 inputs
use punishment-associated PPL101/103/106. These functional subsets follow
[Rubin and Aso (2024), eLife](https://elifesciences.org/articles/90523/figures);
PAM12–14 are not incorrectly treated as generic reward neurons.

### Additional output census (W8)

Counts below are **annotated / retained** after the existing transmitter-sign
policy. Exact `MN11`, `MN12`, `DNg12`, and `MBON08` types have zero bodies;
subtypes must be queried explicitly. Two MN12D bodies have unresolved signs.
DNg11 is a grooming output, not a walking output. All 279 added bodies are real;
no original body is removed. Each circuit remains below 2,000 neurons.

| Circuit | Exact type | Annotated / retained | Reason |
| --- | --- | ---: | --- |
| `olfaction_mb` | MBON02 | 2 / 2 | MB ensemble output; no new valence assignment |
| `olfaction_mb` | MBON07 | 4 / 4 | MB ensemble output; no new valence assignment |
| `olfaction_mb` | MBON08 | 0 / 0 | absent; keep an empty, silent group |
| `olfaction_mb` | MBON09 | 4 / 4 | MB ensemble output; no new valence assignment |
| `olfaction_mb` | MBON10 | 9 / 9 | MB ensemble output; no new valence assignment |
| `olfaction_mb` | MBON13 | 2 / 2 | MB ensemble output; no new valence assignment |
| `olfaction_mb` | MBON15 | 4 / 4 | MB ensemble output; no new valence assignment |
| `olfaction_mb` | MBON16 | 2 / 2 | MB ensemble output; no new valence assignment |
| `olfaction_mb` | MBON17 | 2 / 2 | MB ensemble output; no new valence assignment |
| `olfaction_mb` | MBON18 | 2 / 2 | MB ensemble output; no new valence assignment |
| `olfaction_mb` | MBON19 | 4 / 4 | MB ensemble output; no new valence assignment |
| `olfaction_mb` | MBON20 | 2 / 2 | MB ensemble output; no new valence assignment |
| `olfaction_mb` | MBON21 | 2 / 2 | MB ensemble output; no new valence assignment |
| `olfaction_mb` | MBON22 | 2 / 2 | MB ensemble output; no new valence assignment |
| `olfaction_mb` | MBON23 | 2 / 2 | MB ensemble output; no new valence assignment |
| `olfaction_mb` | MBON24 | 2 / 2 | MB ensemble output; no new valence assignment |
| `olfaction_mb` | MBON25 | 2 / 2 | MB ensemble output; no new valence assignment |
| `olfaction_mb` | MBON26 | 2 / 2 | MB ensemble output; no new valence assignment |
| `olfaction_mb` | MBON27 | 2 / 2 | MB ensemble output; no new valence assignment |
| `olfaction_mb` | MBON28 | 2 / 2 | MB ensemble output; no new valence assignment |
| `olfaction_mb` | MBON29 | 2 / 2 | MB ensemble output; no new valence assignment |
| `olfaction_mb` | MBON30 | 2 / 2 | MB ensemble output; no new valence assignment |
| `olfaction_mb` | MBON31 | 2 / 2 | MB ensemble output; no new valence assignment |
| `olfaction_mb` | MBON32 | 2 / 2 | MB ensemble output; no new valence assignment |
| `olfaction_mb` | MBON33 | 2 / 2 | MB ensemble output; no new valence assignment |
| `olfaction_mb` | MBON34 | 2 / 2 | MB ensemble output; no new valence assignment |
| `olfaction_mb` | MBON35 | 2 / 2 | MB ensemble output; no new valence assignment |
| `feeding` | MN6 | 2 / 2 | labellum extension |
| `feeding` | MN11D | 3 / 3 | fluid ingestion / swallowing |
| `feeding` | MN11V | 2 / 2 | fluid ingestion / swallowing |
| `feeding` | MN12D | 4 / 2 | cibarial pumping; exclude two unresolved signs |
| `steering` | DNa01 | 2 / 2 | bilateral steering readout |
| `steering` | DNb05 | 2 / 2 | bilateral steering readout |
| `steering` | DNb06 | 2 / 2 | bilateral steering readout |
| `steering` | DNg13 | 2 / 2 | bilateral steering readout |
| `grooming` | DNg11 | 6 / 6 | grooming readout |
| `grooming` | DNg12_a | 8 / 8 | grooming readout |
| `grooming` | DNg12_b | 10 / 10 | grooming readout |
| `grooming` | DNg12_c | 8 / 8 | grooming readout |
| `grooming` | DNg12_d | 2 / 2 | grooming readout |
| `grooming` | DNg12_e | 6 / 6 | grooming readout |
| `grooming` | DNg12_f | 4 / 4 | grooming readout |
| `grooming` | DNg12_g | 2 / 2 | grooming readout |
| `grooming` | DNg12_h | 2 / 2 | grooming readout |

MN6 function: [Schwarz et al. (2017)](https://pmc.ncbi.nlm.nih.gov/articles/PMC5315463/).
MN11/MN12 pumping and ingestion: [Manzo et al. (2012)](https://pmc.ncbi.nlm.nih.gov/articles/PMC3341050/).
Steering DNs: [Rayshubskiy et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC10614758/).
Grooming DNs: [Guo et al. (2022)](https://doi.org/10.1016/j.cub.2021.12.055)
and [Cande et al. (2018)](https://pmc.ncbi.nlm.nih.gov/articles/PMC6031430/).
MB ensemble readout: [Aso et al. (2014)](https://pmc.ncbi.nlm.nih.gov/articles/PMC4273436/).
These functions motivate observation, not a claim that activating each cell
uniquely determines a game label. The additional MBONs retain their measured
edges and source signs; only the original ap/av pools undergo the existing
KC normalization and plasticity. Ambiguous MBON `-like` types are not relabeled.

The additional relays below are selected solely by measured two-hop paths to
the new feeding/grooming outputs. Counts are **new bodies by exact type**;
the same path-ranking rationale applies to every entry. The manifest records
each addition, its group, count, and selection reason.

| Circuit | Additional relay types (count per type) |
| --- | --- |
| `feeding` | AN17A008 (1); DNg47 (2); GNG037 (2); GNG055 (2); GNG057 (1); GNG059 (1); GNG065 (2); GNG072 (1); GNG074 (1); GNG076 (1); GNG087 (3); GNG090 (1); GNG096 (1); GNG107 (2); GNG145 (2); GNG147 (1); GNG155 (2); GNG165 (1); GNG170 (2); GNG173 (1); GNG187 (2); GNG192 (2); GNG209 (1); GNG221 (1); GNG232 (2); GNG241 (1); GNG254 (1); GNG298 (1); GNG407 (1); GNG467 (4); GNG468 (1); GNG592 (3); SMP545 (1) |
| `grooming` | AN02A001 (1); AN09B014 (2); AN09B023 (1); AN12B076 (1); AN27X008 (2); ANXXX027 (1); CB0266 (1); CB0397 (1); CB0607 (1); CB0630 (1); CB2205 (4); CB3865 (9); CB4037 (3); CB4038 (1); DNae006 (1); DNde006 (1); DNg05_a (2); DNg05_b (2); DNg08 (1); DNg106 (1); DNg108 (2); DNg32 (1); DNg35 (2); DNg37 (1); DNg48 (2); DNg51 (2); DNg82 (1); DNg83 (2); DNg85 (1); DNge008 (1); DNge032 (1); DNge037 (1); DNge045 (1); DNge056 (2); DNge084 (2); DNge121 (2); DNge122 (1); DNge124 (1); DNge128 (2); DNp73 (1); GNG046 (2); GNG100 (2); GNG102 (2); GNG315 (2); GNG316 (2); GNG423 (1); GNG494 (2); GNG530 (1); GNG547 (2); GNG557 (2); GNG633 (1); GNG666 (1); IPS001 (1); MeVC9 (2); PS126 (2); SAD034 (2); WED167 (2); pIP1 (1) |

Additional steering outputs use the retained 192 visual relay bodies and all
measured induced edges. Longer pathways remain omitted; an added output can
still be silent. The original 200-KC sampling rule is unchanged.

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
is still incomplete. Steering now retains measured three-hop paths; longer
paths and boundary input are omitted. No direct synthetic edge replaces them. A missing population remains an empty, silent group with a
manifest TODO. A test of implementation correctness is not a passed promotion gate.

### Calibration and visual relays

All original synapse identities and source signs are preserved. No thresholds,
learning rates, trait offsets, or cue labels were adjusted. Input rate remains
180 Hz. The global scales are feeding 1/16, escape 1/4096, olfaction 9/64, steering
1/32, and grooming 1/128. Only the MB global scale changes in W8, from 3/16
to 9/64; the seed-19 global-scale sweep and fixed development split are recorded
in [output-scale-sweep.json](reports/output-scale-sweep.json) and
[output-candidate.json](reports/output-candidate.json). The output expansion changes the induced
subgraphs; retained signs and the normalization formulas remain unchanged.

**Mushroom body.** Each MBON's existing KC afferents are multiplied by
`40 / sum(abs(KC weights into that MBON))`. A zero-input column stays zero.
This equalizes total available KC drive without changing afferent ratios or
creating connections. The budget stays fixed at 40, selected by the earlier seed-19 calibration.
W8 does not retune this budget or any individual afferent multiplier.

At the selected MB global scale, the unnormalized APL population fires at
375.625 Hz while the sampled KC population averages 5.7875 Hz. Into **both** MBON pools, APL weights receive the
same factor `mean KC Hz / mean APL Hz = 0.01540765365625975`. Rates come from
one untrained banana/DM1 reference simulation (seed 19, eight trials, 300 ms,
180 Hz); they are not taken from trained states or evaluation seeds. This is
an explicit homeostatic approximation to the sampled circuit's feedback
imbalance. APL→KC and all other MB projections stay unchanged. The manifest
records the reference, budgets, rationale, and every multiplier. New
MaleCNS states should be recreated from this calibrated bundle; prior serialized
states retain their old learned KC magnitudes.

**Steering topology.** In two bounded scans, find sensory→a and b→DNa02 endpoints,
then measured a→b edges. Rank complete paths by the smallest of summed sensory→a,
a→b, and summed b→DNa02 counts, breaking ties by body IDs. Retain whole relay pairs
until the 192-body budget, then retain every measured edge in the induced subgraph.
The original visual relay selection remains; eight additional DN outputs bring
the steering circuit to 332 neurons with no pooling or invented connectivity. The exact
body IDs, 86 relay types, type counts, and selection rule are in the JSON/manifest.
Examples include R8→MeVPLp1→PS059→DNa02 and R8→Tm5c→LLPC1→DNa02;
other retained types include MeLo1/2, Tm37, LT51, LPT22, PS077, and MeVPMe3.
These paths are facts about this extract, not claims of a uniquely identified
phototaxis pathway.

**Steering homeostasis.** Histaminergic photoreceptors keep their negative signs.
A zero-background LIF relay cannot convey an inhibitory signal, so the relay
population and both DNa02 groups receive a shared tonic current of 1.15, the
existing walking model's near-threshold background value. This represents
omitted background drive, not measured connectivity. Within each target, the
available positive and negative afferents are separately normalized to magnitude
4; absent sign strata stay absent. No left/right-specific tuning is used. This
balances excitation/inhibition in the bounded extract and permits disinhibition.
Budgets 2, 4, and 8 were compared at seed 19: 2 gives weak unilateral responses;
4 retains responses without the large spontaneous walking drive seen at 8.
The manifest records both source-sign multiplier vectors and the tonic current.
The small trait effect depends on these explicit model assumptions.

**Decoder features.** The measured version preserves its first 68 output-only features: the eight means, six time windows
for each of the same eight output groups, and six-window right-minus-left and
approach-minus-avoid contrasts. Windows span equal fractions of a trial (50 ms
at the evaluation's 300 ms duration); partial windows are weighted by overlap.
Steering means/windows subtract a neutral simulation of the same individual and
circuit using the original state parameters, including in shuffled controls.
This removes tonic offsets while preserving stimulus responses and walk arousal.
Each of 48 additional readout groups appends one mean and six windows, giving
404 features. MN6, MN11D/V, MN12D, each new DN side/subtype, and each new MBON
type remain separate. The absent MBON08 group contributes zeros. Additional
steering outputs use the same neutral subtraction; no extra tonic currents,
per-cell calibration, or label-dependent features are introduced.
The classifier is unchanged: logistic regression and a 16-hidden-unit tanh MLP,
400 epochs, the original seeds and grouped individual split. The toy checkpoint
retains its eight-feature contract. Measured feature models carry the `malecns-v1.0` version and exact output/window
schema when saved; neither checkpoint can be loaded as the other version.

Measured liked/disliked odor scenarios cycle through banana, apple_vinegar,
yeast, and grape. They no longer label the incomplete blue-light pathway as an
odor preference. All nine behavior labels and all four odors remain, including
silent responses. See the [decoder investigation](reports/decoder-investigation.md)
for diagnosis, independent responsiveness probes, and validation comparisons.

### Reproduce ingestion and evaluation

Run from the repository root. Arrow/pandas are optional ingestion dependencies.

```powershell
.\.tools\uv.exe sync --all-packages --extra ingest
.\.tools\uv.exe run --all-packages --extra ingest python services/brain/scripts/ingest_malecns.py --seed 1729 --scale feeding=0.0625 --scale escape=0.000244140625 --scale olfaction_mb=0.140625 --scale steering=0.03125 --scale grooming=0.0078125
.\.tools\uv.exe run --all-packages --extra ingest python services/brain/scripts/calibrate_malecns.py --output services/brain/reports/calibration-malecns.json
.\.tools\uv.exe run python -m tsuyu_brain.eval --version malecns-v1.0 --output services/brain/reports
.\.tools\uv.exe run pytest
.\.tools\uv.exe run pytest -m eval
.\.tools\uv.exe run ruff check services/brain
.\.tools\uv.exe run ruff format --check services/brain
```

The homeostasis sweep reconstructs integer counts from the bundled factors before
reapplying normalization; the separate raw-source audit verifies those counts
against all three original Feather SHA-256s and every retained edge. Calibration
uses seed 19; evaluation keeps independent seeds 71/81 and its original
individual/decoder seeds. The topology selection never uses simulated behavior.
The final report includes normalization provenance, the output census, and all
confusion matrices. The global-scale probe keeps the existing normalization
formula and budgets fixed. To repeat the preselection MB sweep, run:

```powershell
.\.tools\uv.exe run --all-packages --extra ingest python services/brain/scripts/probe_outputs.py --mb-scale-sweep --output services/brain/reports/output-scale-sweep.json
.\.tools\uv.exe run --all-packages --extra ingest python services/brain/scripts/probe_outputs.py --mb-scale 0.140625 --development --output services/brain/reports/output-candidate.json
```

The recorded `output-probes.json` is the initial expanded extract at MB scale
3/16; `output-candidate.json` evaluates the selected 9/64 candidate. Both use
the original grouped development split. The final test never selects a scale.
A failed promotion gate still exits 1. Passing implementation tests do not waive it.

### Evaluation result for the bundled extract

Full evaluation on PyTorch 2.14.0+cpu: **6/6 gates pass for both versions**.
**`malecns-v1.0` is the default.** The candidate was frozen after development
validation; no adjustment used the final test results. The held-out score
improves from 78.41% logistic / 76.70% MLP to **88.64% for both models**.

| Gate | Result | Measurement |
| --- | --- | --- |
| sugar -> MN9 | pass | 115.625 Hz versus 0 at rest |
| looming -> DNp01 | pass | 25.417 Hz versus 0 at rest |
| bitter suppression | pass | mixed 0 Hz versus sugar 115.625 Hz |
| three-session learning | pass | baseline PI +0.098564; reward shift +0.462885; punishment shift -1.098564 |
| right-turner trait | pass | wild 0.523225 vs trait 0.536174; one-sided p = 0.000857891; 32 flies/group |
| decoder / shuffled control | pass | logistic 88.64%, MLP 88.64%; shuffled 46.59%, 48.86%, 43.75%; average drop 42.23 percentage points |

The unchanged final split is 528/176 rows with test individuals [4, 5, 6, 10];
dataset/split/model seeds are 123/7/11. Both classifiers make 20 errors: eight
approach and eight avoid trials are predicted as rest, plus four left-turn
errors. Feeding is correct on all sixteen held-out trials. Development scores
remain 81.82% for both models, with a finite-sample collision ceiling of 87.88%.
Final models fit twelve individuals and are scored on a different held-out
group from development. The lower validation result and silent yeast responses
remain explicit limitations.

The selected MB global scale 9/64 restores punished vinegar/grape responses in
the independent calibration probe. Yeast activates only four sampled KCs and
no MBON readout after either training valence. Blue-light-to-KC connectivity is
still incomplete. Passing these game-model gates is not biological validation.
The [investigation](reports/decoder-investigation.md) records the full selection
history, anatomy, rejected scales, diagnostics, and remaining limitations.

The measured checkpoint is `decoder/weights/malecns-v1.0.pt`. To reproduce it:

```python
from tsuyu_brain.decoder.dataset import generate_dataset, split_dataset
from tsuyu_brain.decoder.model import train_decoder

train, _ = split_dataset(generate_dataset(version="malecns-v1.0"))
train_decoder(train, "mlp").save("services/brain/src/tsuyu_brain/decoder/weights/malecns-v1.0.pt")
```

Both checkpoints are versioned; existing serialized toy states still use toy
circuits and decoder, including in the activity viewer. New measured states
should be recreated from this calibrated bundle; old experimental measured
states retain their previous learned KC weights.

The final raw-source audit verifies all retained bodies, types, signs, weights,
and input checksums. A fresh ingestion reproduces all eleven bundle files
byte-for-byte. The full Python suite passes 615 tests with MaleCNS as the
default. The full evaluation suite passes all 14 selected tests. Repository-wide
Ruff lint and brain formatting checks pass. No raw data is committed. Validation
commands are listed above.

See [MaleCNS report](reports/report-malecns.md),
[JSON measurements and confusion matrices](reports/report-malecns.json),
[toy report](reports/report.md), and [homeostasis diagnostics](reports/calibration-malecns.json).
