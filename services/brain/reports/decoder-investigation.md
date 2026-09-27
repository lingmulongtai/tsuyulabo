# W8: measured output extraction and decoder investigation

The previous extract confused feed, approach, and avoid with rest. Its fixed
validation sample had 26 unavoidable errors on identical output features
(80.30% empirical ceiling); the final logistic/MLP scores were 78.41%/76.70%.
Those historical scores use the same individuals and four odor scenarios.

## Anatomical expansion

Queries use the local release annotations and the unchanged transmitter policy.
There are no exact MN11, MN12, or DNg12 type names: they are subdivided into
MN11D/V, MN12D, and DNg12_a-h. Two of four MN12D bodies have no supported sign
and are excluded. DNg11 is a grooming output, not a walking output.

The extract adds 132 output neurons: 9 feeding motor neurons, 8 bilateral
steering DNs, 48 grooming DNs, and 67 numbered MBONs. It also adds 51 feeding
and 96 grooming relays on real two-hop sensory-to-new-output paths. All original
bodies remain. All induced edges come from the original Feather synapse counts.
The largest circuit has 1,054 neurons; every circuit remains below 2,000.

The [brain README](../README.md#additional-output-census-w8) lists every type,
count, exclusion, and biological rationale with primary references. The manifest
contains both the annotation census and every added output/relay type with its
selection rule. The source audit checks every retained body/type/sign and edge
against the three original Feather checksums. Text artifacts use LF.

Additional MBONs are individual anatomical readouts, with no unsupported
valence assignment. The original ten approach and ten avoidance MBONs, their
plasticity, 200 sampled KCs, and 200x20 per-fly learned weights stay intact.
MBON08 is absent; its explicit group and features remain zero. The decoder
retains its original 68 features and appends a mean plus six windows for each
of 48 new groups (404 features). It sees output rates only. Both classifier
architectures, epochs, seeds, class weights, and individual splits are unchanged.

## Calibration before final testing

Only the global circuit scale is varied. Input rate remains 180 Hz; thresholds,
traits, learning rate, KC input budget 40, steering sign budget 4, and tonic
currents are fixed. The existing reference-rate normalization formula is
recomputed after each MB global-scale change, with independent seed 19.

The expanded feeding circuit at its original scale 1/16 gives 118.70 Hz MN9
activity for sugar and zero for mixed sugar/bitter in the seed-19, 32-trial
probe. MN11D is strongly responsive. Global feeding scales 3/64, 1/16, 5/64,
3/32, and 1/8 all keep mixed activity zero in that probe. The original 1/16
already separates the stimulus responses and is retained; stronger scales are
not selected merely to increase firing. MN12D remains silent in these probes.

| MB global scale | Banana baseline PI | Reward shift | Punishment shift | Punished vinegar / grape MBON_av Hz |
| ---: | ---: | ---: | ---: | ---: |
| 0.09375 | +0.248 | +0.347 | -1.248 | 3.000 / 3.667 |
| 0.140625 | +0.098 | +0.469 | -1.098 | 1.917 / 1.625 |
| 0.1875 | +0.100 | +0.436 | -1.100 | 0.000 / 0.000 |
| 0.234375 | +0.120 | +0.420 | -1.120 | 0.000 / 0.000 |
| 0.28125 | +0.201 | +0.322 | -1.201 | 0.000 / 0.000 |
| 0.375 | +0.129 | +0.300 | -1.129 | 0.000 / 0.000 |

Select 9/64 (0.140625): it restores punished vinegar/grape output while keeping
banana close to neutral and both learning shifts beyond 0.3 in calibration.
The smaller 3/32 scale has a banana baseline outside the existing +/-0.2
regression bound. Higher scales do not recover weak-odor avoidance. Yeast is
silent at every tested scale. This is a limited documented sweep, not a claim
that all possible global scales have been exhausted.

| Fixed development candidate | Logistic | MLP | Identical-feature ceiling |
| --- | ---: | ---: | ---: |
| Previous extract | 79.55% | 78.79% | 80.30% |
| Expanded outputs, original scales | 81.82% | 81.82% | 84.85% |
| Expanded outputs, MB 9/64 (selected) | 81.82% | 81.82% | 87.88% |

The selected scale ties validation accuracy and reduces silent response
collisions from 20 to 16 rows out of 132. This responsiveness improvement and
the independent calibration determine selection; no final test score selects
a scale. Fit IDs remain [0, 3, 7, 8, 9, 11, 12, 13, 15], validation [1, 2, 14],
and final test [4, 5, 6, 10]. Final refitting uses all twelve training IDs.

Validation still misses all twelve avoidance trials: eight are exactly silent;
the four nonzero responses are too weak to generalize with the frozen training
procedure. Eight approach trials are silent, and four left-turn trials are
misclassified. All feed and rest validation rows are correct. No labels or
silent trials are dropped. Finite-sample collision ceilings are not estimates
of population accuracy.

## Remaining mechanism

At the selected scale, the independent yeast probe activates only 4/200 KCs
(population mean 1.113 Hz) while APL fires at 263.333 Hz. PN activity is
46.944 Hz, so sensory activity reaches the circuit, but none of the MBON
outputs fires after either training valence. These observations are consistent
with inadequate sampled KC drive relative to inhibition in this LIF reduction;
adding all available exact numbered MBON types does not itself repair it.
This diagnoses the model, not real fly physiology. Longer pathways, boundary
input, and more representative upstream sampling remain possible future work.

Raw measurements: [initial probes](output-probes.json),
[global scale sweep](output-scale-sweep.json),
[candidate validation](output-candidate.json), and
[final upstream/output probes](output-final-probes.json).
The probe script is `services/brain/scripts/probe_outputs.py`; ingestion and
evaluation commands are in the brain README.

## Frozen final result and promotion

Both classifiers score **88.64%** on the unchanged 176-row test set. Shuffled
MLP scores are 46.59%, 48.86%, and 43.75% (mean drop 42.23 percentage points).
All six gates pass for both MaleCNS and toy. MaleCNS becomes the default with a
version-matched MLP checkpoint trained on the same twelve final training IDs.
The prior toy checkpoint and explicit/persisted toy states remain supported.

Both final confusion matrices have 20 errors: eight approach and eight avoid
rows collapse to rest, plus four left-turn errors (rest for logistic, avoid for
MLP). All sixteen feeding trials are correct. No neural scale, classifier hyperparameter, or feature change
was selected after these results. Final models fit twelve individuals and are
scored on a different held-out group from the development fit. The 81.82%
validation score remains explicit alongside the passing test result.

The versioned [MaleCNS report](report-malecns.md) and [toy report](report.md)
contain all six gate results and frozen controls. The activity facade now uses
each persisted state's version for every circuit while keeping the viewer's
23-group public contract. The output additions are decoder readouts, not a
redesign of that viewer.

Promotion also preserves the API's compact-state contract. Measured float16
weights are stored as compressed XOR deltas with a SHA-256-bound baseline;
restoration recovers the exact dense float16 bits without replaying training.
Legacy toy and uncompressed measured states remain readable. Checkpoint loading
verifies version and exact feature ordering. Toy-specific topology and
plasticity tests now request toy fixtures explicitly; default facade and full
API/worker/Shiori tests run with the promoted measured version.

Final verification with MaleCNS as default: `uv run pytest` passes 615 tests;
`uv run pytest -m eval` passes all 14 selected evaluations. Repository-wide
Ruff lint, brain formatting, and whitespace checks pass. A fresh ingestion
reproduces every bundle file byte-for-byte; raw data remains uncommitted.
