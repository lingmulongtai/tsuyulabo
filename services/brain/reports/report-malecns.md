# Brain evaluation — malecns-v1.0

Game LIF evaluation; measured MaleCNS topology or synthetic toy topology. This is not biological validation.

| Check | Pass | Measurements |
| --- | --- | --- |
| sugar_mn9 | True | `{"rest_hz": 0.0, "sugar_hz": 2.9166667461395264}` |
| looming_dnp01 | True | `{"rest_hz": 0.0, "looming_hz": 25.41666603088379}` |
| bitter_suppression | True | `{"sugar_hz": 2.9166667461395264, "mixed_hz": 1.1458333730697632}` |
| learning | True | `{"baseline_pi": 0.08268728852272034, "reward_delta": 0.47124776244163513, "punish_delta": -1.0826872885227203}` |
| trait_bias | True | `{"wild_mean_right_fraction": 0.5237445188686252, "trait_mean_right_fraction": 0.5391871053725481, "p_one_sided": 1.3848451504502263e-05, "individuals_per_group": 32}` |
| decoder | False | `{"train_rows": 528, "test_rows": 176, "feature_count": 68, "feature_schema": "eight means + six windows per output + right-left/approach-avoid windows", "accuracy_drop": 0.378787895043691, "minimum_drop": 0.1}` |

## Decoder

| Model | Accuracy |
| --- | ---: |
| logistic | 75.57% |
| mlp | 78.98% |
| shuffled_41 | 43.18% |
| shuffled_42 | 40.34% |
| shuffled_43 | 39.77% |

### logistic confusion matrix

| True / predicted | rest | walk | turn_left | turn_right | feed | escape | groom | approach | avoid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rest | 34 | 9 | 0 | 0 | 5 | 0 | 0 | 0 | 0 |
| walk | 0 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| turn_left | 0 | 0 | 12 | 1 | 3 | 0 | 0 | 0 | 0 |
| turn_right | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| feed | 9 | 0 | 0 | 0 | 7 | 0 | 0 | 0 | 0 |
| escape | 0 | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 |
| groom | 4 | 0 | 0 | 0 | 0 | 0 | 12 | 0 | 0 |
| approach | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 12 | 0 |
| avoid | 4 | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 8 |

### mlp confusion matrix

| True / predicted | rest | walk | turn_left | turn_right | feed | escape | groom | approach | avoid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rest | 37 | 0 | 0 | 0 | 11 | 0 | 0 | 0 | 0 |
| walk | 0 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| turn_left | 3 | 0 | 13 | 0 | 0 | 0 | 0 | 0 | 0 |
| turn_right | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| feed | 9 | 0 | 0 | 0 | 7 | 0 | 0 | 0 | 0 |
| escape | 0 | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 |
| groom | 2 | 0 | 0 | 0 | 0 | 0 | 14 | 0 | 0 |
| approach | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 12 | 0 |
| avoid | 4 | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 8 |

### shuffled_41 confusion matrix

| True / predicted | rest | walk | turn_left | turn_right | feed | escape | groom | approach | avoid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rest | 5 | 0 | 8 | 0 | 31 | 0 | 0 | 4 | 0 |
| walk | 4 | 12 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| turn_left | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 | 0 |
| turn_right | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 | 0 |
| feed | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 |
| escape | 0 | 0 | 4 | 0 | 0 | 11 | 0 | 1 | 0 |
| groom | 4 | 0 | 8 | 0 | 0 | 0 | 0 | 4 | 0 |
| approach | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 12 |
| avoid | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 4 | 12 |

### shuffled_42 confusion matrix

| True / predicted | rest | walk | turn_left | turn_right | feed | escape | groom | approach | avoid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rest | 0 | 0 | 16 | 0 | 32 | 0 | 0 | 0 | 0 |
| walk | 0 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| turn_left | 3 | 0 | 0 | 10 | 0 | 0 | 0 | 1 | 2 |
| turn_right | 0 | 0 | 0 | 15 | 0 | 0 | 0 | 1 | 0 |
| feed | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 |
| escape | 0 | 0 | 4 | 0 | 0 | 12 | 0 | 0 | 0 |
| groom | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 | 0 |
| approach | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 8 | 4 |
| avoid | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 8 | 4 |

### shuffled_43 confusion matrix

| True / predicted | rest | walk | turn_left | turn_right | feed | escape | groom | approach | avoid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rest | 9 | 5 | 0 | 0 | 28 | 0 | 0 | 6 | 0 |
| walk | 0 | 12 | 0 | 0 | 0 | 0 | 0 | 0 | 4 |
| turn_left | 1 | 0 | 12 | 0 | 1 | 0 | 0 | 2 | 0 |
| turn_right | 10 | 0 | 0 | 0 | 3 | 0 | 0 | 2 | 1 |
| feed | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 |
| escape | 0 | 0 | 0 | 1 | 3 | 9 | 0 | 3 | 0 |
| groom | 4 | 4 | 0 | 0 | 4 | 0 | 0 | 4 | 0 |
| approach | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 12 | 0 |
| avoid | 4 | 0 | 0 | 0 | 0 | 0 | 0 | 12 | 0 |

Decoder confusion matrices: rows = true, columns = predicted; labels in JSON.
Shuffled controls preserve each projection's weights (including zeros).
The decoder is frozen; three control seeds use the same held-out individuals.
A 10 percentage-point average drop operationalizes 'large drop' for this model.
