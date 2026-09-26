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
- A fly stores only parameters and 200×2 KC→MBON weights. Versioned JSON bytes
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

The control permutes **all entries, including zeros, within each projection**,
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

## Future MaleCNS ingestion (offline skeleton)

Data source: [official MaleCNS downloads](https://male-cns.janelia.org/download/),
dataset `male-cns:v1.0`, released under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
Attribution: FlyEM (HHMI Janelia), University of Cambridge, MRC Laboratory of
Molecular Biology, and Google Research. Cite the dataset and the
[MaleCNS paper linked by the project](https://www.cell.com/cell/fulltext/S0092-8674%2826%2900942-6)
when distributing derivatives. The [project page](https://male-cns.janelia.org/)
maintains publication and release information.

No real connectome is included or downloaded by this package. A human must obtain
the official annotations, neurotransmitter predictions, and connectivity export;
select a small circuit; review aliases, laterality, and transmitter/receptor signs;
and normalize those records into local CSV files:

```text
neurons.csv: body_id,group,sign
edges.csv:   pre,post,synapses
```

`sign` must be +1 or -1, with no automatic assumption for uncertain transmitters.
The script intentionally leaves official Feather/schema adaptation, biological
curation, and current calibration as TODOs. It requires an explicit weight scale.

```powershell
.\.tools\uv.exe run python services/brain/scripts/ingest_malecns.py --help
# After preparing local, normalized extracts:
.\.tools\uv.exe run python services/brain/scripts/ingest_malecns.py --neurons services/brain/data/raw/neurons.csv --edges services/brain/data/raw/edges.csv --output services/brain/data/cache/feeding.npz --name feeding --inputs Gr64f Gr66a --outputs MN9 --weight-scale 0.01
```

The output is a SciPy CSR `.npz` plus JSON group/sign metadata, provenance,
normalization scale, and source-file hashes. `load_npz_circuit(Path(...))` in
`connectome.npz_io` returns the same `Circuit` interface. Extracts are limited to
2,000 cells; omitted boundary edges and Dale-style signs are explicit model
assumptions. Unvalidated extracts use `malecns-v1.0-unvalidated` and are not added
to the game registry. Real-data calibration and decoder retraining remain future
work; never substitute them silently for `toy-v0`.
