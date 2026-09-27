# Brain evaluation — malecns-v1.0

Game LIF evaluation; measured MaleCNS topology or synthetic toy topology. This is not biological validation.

| Check | Pass | Measurements |
| --- | --- | --- |
| sugar_mn9 | True | `{"rest_hz": 0.0, "sugar_hz": 2.9166667461395264}` |
| looming_dnp01 | True | `{"rest_hz": 0.0, "looming_hz": 25.41666603088379}` |
| bitter_suppression | True | `{"sugar_hz": 2.9166667461395264, "mixed_hz": 1.1458333730697632}` |
| learning | False | `{"baseline_pi": 1.0, "reward_delta": 0.0, "punish_delta": -1.0}` |
| trait_bias | False | `{"wild_mean_right_fraction": 0.0, "trait_mean_right_fraction": 0.0, "p_one_sided": null, "individuals_per_group": 32}` |
| decoder | False | `{"train_rows": 528, "test_rows": 176, "accuracy_drop": 0.05681818723678589, "minimum_drop": 0.1}` |

## Decoder

| Model | Accuracy |
| --- | ---: |
| logistic | 46.59% |
| mlp | 46.59% |
| shuffled_41 | 40.91% |
| shuffled_42 | 40.91% |
| shuffled_43 | 40.91% |

### logistic confusion matrix

| True / predicted | rest | walk | turn_left | turn_right | feed | escape | groom | approach | avoid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rest | 0 | 0 | 21 | 0 | 6 | 0 | 0 | 0 | 21 |
| walk | 0 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| turn_left | 0 | 0 | 8 | 0 | 0 | 0 | 0 | 0 | 8 |
| turn_right | 0 | 0 | 8 | 0 | 0 | 0 | 0 | 0 | 8 |
| feed | 0 | 0 | 5 | 0 | 10 | 0 | 0 | 0 | 1 |
| escape | 0 | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 |
| groom | 0 | 0 | 0 | 0 | 0 | 0 | 16 | 0 | 0 |
| approach | 0 | 0 | 4 | 0 | 0 | 0 | 0 | 8 | 4 |
| avoid | 0 | 0 | 8 | 0 | 0 | 0 | 0 | 0 | 8 |

### mlp confusion matrix

| True / predicted | rest | walk | turn_left | turn_right | feed | escape | groom | approach | avoid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rest | 0 | 0 | 0 | 42 | 6 | 0 | 0 | 0 | 0 |
| walk | 0 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| turn_left | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| turn_right | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| feed | 0 | 0 | 0 | 6 | 10 | 0 | 0 | 0 | 0 |
| escape | 0 | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 |
| groom | 0 | 0 | 0 | 0 | 0 | 0 | 16 | 0 | 0 |
| approach | 0 | 0 | 0 | 8 | 0 | 0 | 0 | 8 | 0 |
| avoid | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |

### shuffled_41 confusion matrix

| True / predicted | rest | walk | turn_left | turn_right | feed | escape | groom | approach | avoid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rest | 0 | 0 | 0 | 16 | 32 | 0 | 0 | 0 | 0 |
| walk | 0 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| turn_left | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| turn_right | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| feed | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 |
| escape | 0 | 0 | 0 | 2 | 0 | 12 | 0 | 2 | 0 |
| groom | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| approach | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 12 | 0 |
| avoid | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 12 | 0 |

### shuffled_42 confusion matrix

| True / predicted | rest | walk | turn_left | turn_right | feed | escape | groom | approach | avoid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rest | 0 | 0 | 0 | 16 | 32 | 0 | 0 | 0 | 0 |
| walk | 0 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| turn_left | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| turn_right | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| feed | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 |
| escape | 0 | 0 | 0 | 3 | 0 | 12 | 0 | 1 | 0 |
| groom | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| approach | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 12 | 0 |
| avoid | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 12 | 0 |

### shuffled_43 confusion matrix

| True / predicted | rest | walk | turn_left | turn_right | feed | escape | groom | approach | avoid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rest | 0 | 0 | 0 | 23 | 25 | 0 | 0 | 0 | 0 |
| walk | 0 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| turn_left | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| turn_right | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| feed | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 |
| escape | 0 | 0 | 0 | 3 | 0 | 12 | 0 | 1 | 0 |
| groom | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| approach | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 12 | 0 |
| avoid | 0 | 0 | 0 | 4 | 0 | 0 | 0 | 12 | 0 |

Decoder confusion matrices: rows = true, columns = predicted; labels in JSON.
Shuffled controls preserve each projection's weights (including zeros).
The decoder is frozen; three control seeds use the same held-out individuals.
A 10 percentage-point average drop operationalizes 'large drop' for this model.
