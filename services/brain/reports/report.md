# Brain evaluation — toy-v0

Game LIF evaluation; measured MaleCNS topology or synthetic toy topology. This is not biological validation.

| Check | Pass | Measurements |
| --- | --- | --- |
| sugar_mn9 | True | `{"rest_hz": 0.0, "sugar_hz": 326.7708435058594}` |
| looming_dnp01 | True | `{"rest_hz": 0.0, "looming_hz": 318.125}` |
| bitter_suppression | True | `{"sugar_hz": 326.7708435058594, "mixed_hz": 0.0}` |
| learning | True | `{"baseline_pi": 0.0, "reward_delta": 1.0, "punish_delta": -1.0}` |
| trait_bias | True | `{"wild_mean_right_fraction": 0.5221496904268861, "trait_mean_right_fraction": 0.600973891094327, "p_one_sided": 7.436589328947562e-32, "individuals_per_group": 32}` |
| decoder | True | `{"train_rows": 528, "test_rows": 176, "feature_count": 8, "feature_schema": "eight output means", "accuracy_drop": 0.22537879149119056, "minimum_drop": 0.1}` |

## Fixed evaluation protocol

Dataset seed 123; split seed 7; model seed 11; 400 epochs. Splits are grouped by individual.

Development fit: [0, 3, 7, 8, 9, 11, 12, 13, 15]; validation: [1, 2, 14].
Final training: [0, 1, 2, 3, 7, 8, 9, 11, 12, 13, 14, 15]; test: [4, 5, 6, 10].

changes selected using development fit/validation only; final models refit on all training individuals; test and controls evaluated frozen.

## Development diagnostics

training_diagnostics: `{"rows": 528, "unavoidable_errors_from_identical_features": 0, "empirical_accuracy_ceiling": 1.0, "zero_feature_rows_by_label": {"rest": 12, "walk": 0, "turn_left": 0, "turn_right": 0, "feed": 0, "escape": 0, "groom": 0, "approach": 0, "avoid": 0}}`

validation_diagnostics: `{"rows": 132, "unavoidable_errors_from_identical_features": 0, "empirical_accuracy_ceiling": 1.0, "zero_feature_rows_by_label": {"rest": 0, "walk": 0, "turn_left": 0, "turn_right": 0, "feed": 0, "escape": 0, "groom": 0, "approach": 0, "avoid": 0}}`

Validation logistic: 100.00%.
Validation mlp: 100.00%.

The collision ceiling applies only to the observed finite sample. Zero features mean no evoked output, not that every neuron is silent.

## Decoder

| Model | Accuracy |
| --- | ---: |
| logistic | 100.00% |
| mlp | 100.00% |
| shuffled_41 | 75.00% |
| shuffled_42 | 84.09% |
| shuffled_43 | 73.30% |

### logistic confusion matrix

| True / predicted | rest | walk | turn_left | turn_right | feed | escape | groom | approach | avoid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rest | 48 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| walk | 0 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| turn_left | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 | 0 |
| turn_right | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| feed | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 |
| escape | 0 | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 |
| groom | 0 | 0 | 0 | 0 | 0 | 0 | 16 | 0 | 0 |
| approach | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 16 | 0 |
| avoid | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 16 |

### mlp confusion matrix

| True / predicted | rest | walk | turn_left | turn_right | feed | escape | groom | approach | avoid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rest | 48 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| walk | 0 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| turn_left | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 | 0 |
| turn_right | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| feed | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 |
| escape | 0 | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 |
| groom | 0 | 0 | 0 | 0 | 0 | 0 | 16 | 0 | 0 |
| approach | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 16 | 0 |
| avoid | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 16 |

### shuffled_41 confusion matrix

| True / predicted | rest | walk | turn_left | turn_right | feed | escape | groom | approach | avoid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rest | 48 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| walk | 0 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| turn_left | 0 | 14 | 2 | 0 | 0 | 0 | 0 | 0 | 0 |
| turn_right | 0 | 14 | 0 | 2 | 0 | 0 | 0 | 0 | 0 |
| feed | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 |
| escape | 0 | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 |
| groom | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| approach | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 16 | 0 |
| avoid | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 16 |

### shuffled_42 confusion matrix

| True / predicted | rest | walk | turn_left | turn_right | feed | escape | groom | approach | avoid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rest | 48 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| walk | 0 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| turn_left | 0 | 9 | 7 | 0 | 0 | 0 | 0 | 0 | 0 |
| turn_right | 0 | 10 | 0 | 6 | 0 | 0 | 0 | 0 | 0 |
| feed | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 |
| escape | 0 | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 |
| groom | 7 | 0 | 0 | 0 | 0 | 0 | 9 | 0 | 0 |
| approach | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 14 | 2 |
| avoid | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 16 |

### shuffled_43 confusion matrix

| True / predicted | rest | walk | turn_left | turn_right | feed | escape | groom | approach | avoid |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| rest | 48 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| walk | 0 | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| turn_left | 0 | 15 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| turn_right | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 | 0 |
| feed | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 | 0 |
| escape | 0 | 0 | 0 | 0 | 0 | 16 | 0 | 0 | 0 |
| groom | 16 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| approach | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 8 | 0 |
| avoid | 8 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 8 |

Decoder confusion matrices: rows = true, columns = predicted; labels in JSON.
Shuffled controls preserve each projection's weights (including zeros).
The decoder is frozen; three control seeds use the same held-out individuals.
A 10 percentage-point average drop operationalizes 'large drop' for this model.
