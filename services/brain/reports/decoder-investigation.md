# MaleCNS decoder investigation

This is an evaluation of the game's sampled LIF circuits, not biological validation.
The test split was not used to select these changes. The previously committed
test confusion matrix was used only to identify the initial failure categories.

## Fixed protocol

- Dataset seed 123; individual seed `123 + 1009 * individual`; four trials for
  each of eleven scenarios; all nine behavior labels retained.
- Outer split seed 7: final training individuals
  `[0, 1, 2, 3, 7, 8, 9, 11, 12, 13, 14, 15]`; test `[4, 5, 6, 10]`.
- Inner grouped split, also seed 7: fit `[0, 3, 7, 8, 9, 11, 12, 13, 15]`;
  validation `[1, 2, 14]`. This gives 396 fit, 132 validation, and 176 test rows.
- Classifiers remain logistic regression and a 16-unit tanh MLP, model seed 11,
  Adam learning rate 0.04, 400 epochs, and the existing class-balanced loss.
  Standardization uses fitting rows only. Final models are refit on all 528
  development rows after selection and frozen for test and shuffle seeds 41–43.

## What collapses

The old MLP test matrix has 37 errors: 20 rest/feed confusions, 12 missed
approach/avoid trials, three missed left turns, and two missed grooming trials.
The original *training* data has 22/48 sugar trials with zero MN9 activity,
20/48 approach trials with zero approach output, and 40/48 avoidance trials
with zero avoidance output. Turning is not the main test failure.

The dataset also used `blue_light` for liked/disliked **odor** scenarios, despite
the extract's incomplete visual-to-KC path. Both resulting MBON outputs are
zero. The measured dataset now cycles through all four actual odor encodings;
it does not remove weak odors, discard difficult trials, or relabel silent
trials as rest. The toy dataset and checkpoint retain their existing contract.

Silence is not limited to blue light. For a wild-type female generated with
individual seed 123, simulation seed 123, four trials, and three
reward/punishment sessions (seeds 123–125), mean MBON rates (approach/avoid Hz) are:

| Cue | Reward | Punishment |
| --- | --- | --- |
| banana | 36.667 / 10.333 | 0 / 1.750 |
| apple_vinegar | 17.750 / 3.667 | 0 / 0 |
| yeast | 0 / 0 | 0 / 0 |
| grape | 16.250 / 3.000 | 0 / 0 |
| blue_light | 0 / 0 | 0 / 0 |

These are sampled-circuit responses, not claims that real flies cannot respond
to these cues. The independent seed-19 probes below confirm that simply raising
input rate does not repair the weak MB routes.

## Responsiveness probes before feature changes

Feeding calibration used default parameters, seed 19, 32 trials, and 300 ms.
Only `input_rate_hz` was changed; stimulus intensity was 1 for each active GRN.

| Input Hz | Sugar MN9 Hz | Sugar silent trials | Sugar+bitter MN9 Hz |
| ---: | ---: | ---: | ---: |
| 180 | 2.500 | 10 | 0.573 |
| 202.5 | 5.156 | 1 | 1.458 |
| 225 | 10.885 | 0 | 3.594 |
| 270 | 26.198 | 0 | 10.417 |
| 360 | 55.260 | 0 | 36.719 |
| 720 | 102.031 | 0 | 76.250 |

Higher rates restore feeding spikes but also increase the response assigned to
the `sugar+bitter` rest scenario. At 360 and 720 Hz, mixed responses exceed 50%
of sugar responses, failing the existing bitter-suppression criterion in this
calibration probe. The smaller 225/270 Hz candidates were evaluated on the fixed
development split (feeding scenarios only) and did not improve validation.

MB probes used seed 19, eight trials, three training sessions (seeds 19–21),
300 ms, and input rates 225, 270, and 360 Hz. Yeast stays at 0/0 MBON Hz at all
three rates, despite about 1 Hz mean KC activity and 292 Hz APL activity.
Punished apple_vinegar and grape also remain at 0/0. Increasing the input rate
does not overcome this sampled circuit's feedback/drive imbalance.

An additional independent probe multiplied both existing APL→MBON projection
gains by 0.5 or 0.25, preserving all signs and edges. It restores punished
apple_vinegar/grape output but still leaves yeast silent. Banana's untrained
PI shifts to −0.414 or −0.702, outside the existing neutral-baseline regression's
target (`abs(PI) < 0.2`); the 0.25 probe also leaves less than a −0.3 punishment shift.
Neither feedback change was adopted. No wiring, input-rate, threshold,
plasticity, or trait calibration changes are included in this branch.

## Selected features and validation

The existing 68 output-only features retain eight means, six windows per output,
and windowed right-minus-left / approach-minus-avoid differences. The measured
steering means/windows now subtract a neutral simulation of the same individual
and circuit with **original** state parameters. The walk arousal increment is
therefore retained. Controls use their own shuffled neutral circuit. No label,
scenario ID, individual ID, or raw individual parameter is supplied to a model.

The neutral probe is deterministic without sensory input. This removes individual
tonic offsets that previously confused validation rest and left-turn trials.
All three turning/walking labels are correctly decoded on validation after
centering. The toy feature schema and inference remain unchanged.

| Development candidate | Logistic validation | MLP validation |
| --- | ---: | ---: |
| Original dataset/features | 59.09% | 58.33% |
| Four odor cues, raw steering | 61.36% | 67.42% |
| Four odor cues, neutral-centered steering (selected) | 79.55% | 78.79% |
| Selected features, feeding input ×1.25 | 68.94% | 75.76% |
| Selected features, feeding input ×1.5 | 68.94% | 78.03% |

The selected validation sample contains **26 unavoidable errors out of 132**:
identical feature vectors occur under different true labels. Even a hypothetical
unlimited-capacity deterministic classifier cannot exceed **80.30% on this
finite sample**. This is an empirical collision bound, not a population estimate.
Zero evoked features occur in 33 rest, four feed, eight approach, and twelve avoid
rows; additional nonzero feature collisions also contribute to the bound.
The corresponding full training-sample ceiling is 85.98% (74 unavoidable errors
in 528 rows). Model capacity/early-stopping sweeps cannot resolve these exact
collisions, so they were not used to optimize against the test split.

## Reproduction and remaining work

The frozen candidate's final test accuracy is **78.41% logistic / 76.70% MLP**;
shuffled MLP scores are **48.30%, 46.02%, and 51.14%** (mean drop 28.22 points).
The MLP makes 41 errors: 13 rest/feed confusions, 24 missed odor labels, and four
left-to-right turn confusions. All other five MaleCNS gates still pass.
`toy-v0` remains the default. The best new held-out score is 78.41%; the earlier
dataset's historical best was 78.98% MLP. The cue assignment has changed, so these
are not measurements of an identical scenario sample. The development gain did
not translate into a better final test score; there was no further tuning after
this result and no promotion or experimental checkpoint.

Run from the repository root:

```powershell
.\.tools\uv.exe run python -m tsuyu_brain.eval --version malecns-v1.0 --output services/brain/reports
.\.tools\uv.exe run python -m tsuyu_brain.eval --version toy-v0
.\.tools\uv.exe run pytest
.\.tools\uv.exe run pytest -m eval
.\.tools\uv.exe run ruff check .
.\.tools\uv.exe run ruff format --check services/brain
```

The generated [report](report-malecns.md) includes final test/control confusion
matrices, the exact split, validation scores, and collision counts. Its
[JSON](report-malecns.json) also includes validation confusion matrices. The
evaluation CLI exits 1 if the promotion gate fails; passing regression tests
does not waive that gate.

Further improvement needs a circuit model/extract that preserves output activity
for weak odors and distinguishes sugar from partially suppressed feeding across
individuals. Removing those trials or silently weakening the gate would conceal
the limitation. Raw Feather inputs are not modified or committed; bundled
weights and their SHA-256s are unchanged. Text reports and updated manifest
metadata use LF line endings.
