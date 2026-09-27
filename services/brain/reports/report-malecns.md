# Brain evaluation — malecns-v1.0

Game LIF evaluation; measured MaleCNS topology or synthetic toy topology. This is not biological validation.

| Check | Pass | Measurements |
| --- | --- | --- |
| sugar_mn9 | True | `{"rest_hz": 0.0, "sugar_hz": 2.9166667461395264}` |
| looming_dnp01 | True | `{"rest_hz": 0.0, "looming_hz": 25.41666603088379}` |
| bitter_suppression | True | `{"sugar_hz": 2.9166667461395264, "mixed_hz": 1.1458333730697632}` |
| learning | True | `{"baseline_pi": 0.08268728852272034, "reward_delta": 0.47124776244163513, "punish_delta": -1.0826872885227203}` |
| trait_bias | True | `{"wild_mean_right_fraction": 0.5237445188686252, "trait_mean_right_fraction": 0.5391871053725481, "p_one_sided": 1.3848451504502263e-05, "individuals_per_group": 32}` |
| decoder | False | `{"train_rows": 528, "test_rows": 176, "feature_count": 68, "feature_schema": "eight means + six windows per output + right-left/approach-avoid windows; steering centered on individual neutral activity", "accuracy_drop": 0.28219695885976154, "minimum_drop": 0.1}` |

## Fixed evaluation protocol

Dataset seed 123; split seed 7; model seed 11; 400 epochs. Splits are grouped by individual.

Development fit: [0, 3, 7, 8, 9, 11, 12, 13, 15]; validation: [1, 2, 14].
Final training: [0, 1, 2, 3, 7, 8, 9, 11, 12, 13, 14, 15]; test: [4, 5, 6, 10].

changes selected using development fit/validation only; final models refit on all training individuals; test and controls evaluated frozen.

## Development diagnostics

training_diagnostics: `{"rows": 528, "unavoidable_errors_from_identical_features": 74, "empirical_accuracy_ceiling": 0.8598484848484849, "zero_feature_rows_by_label": {"rest": 131, "walk": 0, "turn_left": 0, "turn_right": 0, "feed": 22, "escape": 0, "groom": 0, "approach": 8, "avoid": 37}}`

validation_diagnostics: `{"rows": 132, "unavoidable_errors_from_identical_features": 26, "empirical_accuracy_ceiling": 0.803030303030303, "zero_feature_rows_by_label": {"rest": 33, "walk": 0, "turn_left": 0, "turn_right": 0, "feed": 4, "escape": 0, "groom": 0, "approach": 8, "avoid": 12}}`

Validation logistic: 79.55%.
Validation mlp: 78.79%.

The collision ceiling applies only to the observed finite sample. Zero features mean no evoked output, not that every neuron is silent.

## Decoder

| Model | Accuracy |
| --- | ---: |
| logistic | 78.41% |
| mlp | 76.70% |
| shuffled_41 | 48.30% |
| shuffled_42 | 46.02% |
| shuffled_43 | 51.14% |

### logistic confusion matrix

| True / predicted | rest | walk | turn_left | turn_right | feed | escape | groom | approach | avoid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rest | 45 | 0 | 0 | 0 | 3 | 0 | 0 | 0 | 0 |
| walk | 0 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| turn_left | 0 | 0 | 12 | 1 | 0 | 0 | 0 | 0 | 3 |
| turn_right | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| feed | 7 | 0 | 0 | 0 | 9 | 0 | 0 | 0 | 0 |
| escape | 0 | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 |
| groom | 0 | 0 | 0 | 0 | 0 | 0 | 16 | 0 | 0 |
| approach | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 8 | 0 |
| avoid | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

### mlp confusion matrix

| True / predicted | rest | walk | turn_left | turn_right | feed | escape | groom | approach | avoid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rest | 44 | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 0 |
| walk | 0 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| turn_left | 0 | 0 | 12 | 4 | 0 | 0 | 0 | 0 | 0 |
| turn_right | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| feed | 9 | 0 | 0 | 0 | 7 | 0 | 0 | 0 | 0 |
| escape | 0 | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 |
| groom | 0 | 0 | 0 | 0 | 0 | 0 | 16 | 0 | 0 |
| approach | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 8 | 0 |
| avoid | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

### shuffled_41 confusion matrix

| True / predicted | rest | walk | turn_left | turn_right | feed | escape | groom | approach | avoid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rest | 16 | 0 | 0 | 0 | 32 | 0 | 0 | 0 | 0 |
| walk | 0 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| turn_left | 1 | 3 | 8 | 3 | 0 | 0 | 0 | 0 | 1 |
| turn_right | 3 | 0 | 12 | 1 | 0 | 0 | 0 | 0 | 0 |
| feed | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 |
| escape | 4 | 0 | 0 | 0 | 0 | 12 | 0 | 0 | 0 |
| groom | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| approach | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 16 |
| avoid | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 16 |

### shuffled_42 confusion matrix

| True / predicted | rest | walk | turn_left | turn_right | feed | escape | groom | approach | avoid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rest | 16 | 0 | 0 | 0 | 32 | 0 | 0 | 0 | 0 |
| walk | 0 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| turn_left | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 11 | 4 |
| turn_right | 0 | 0 | 0 | 2 | 0 | 4 | 0 | 10 | 0 |
| feed | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 |
| escape | 4 | 0 | 0 | 0 | 0 | 12 | 0 | 0 | 0 |
| groom | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| approach | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 13 |
| avoid | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 16 |

### shuffled_43 confusion matrix

| True / predicted | rest | walk | turn_left | turn_right | feed | escape | groom | approach | avoid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rest | 25 | 0 | 0 | 0 | 23 | 0 | 0 | 0 | 0 |
| walk | 0 | 12 | 0 | 0 | 0 | 0 | 4 | 0 | 0 |
| turn_left | 5 | 0 | 9 | 0 | 0 | 0 | 0 | 1 | 1 |
| turn_right | 12 | 0 | 0 | 0 | 0 | 0 | 0 | 3 | 1 |
| feed | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 |
| escape | 4 | 0 | 0 | 0 | 0 | 12 | 0 | 0 | 0 |
| groom | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| approach | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 16 | 0 |
| avoid | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 16 | 0 |

Decoder confusion matrices: rows = true, columns = predicted; labels in JSON.
Shuffled controls preserve each projection's weights (including zeros).
The decoder is frozen; three control seeds use the same held-out individuals.
A 10 percentage-point average drop operationalizes 'large drop' for this model.
