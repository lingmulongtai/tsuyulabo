from __future__ import annotations

import pytest
import torch
from tsuyu_brain.behavior import LABELS, SCENARIOS
from tsuyu_brain.decoder import dataset


@pytest.mark.parametrize("version", ["toy-v0", "malecns-v1.0"])
def test_dataset_labels_only_supported_cues(version: str, monkeypatch: pytest.MonkeyPatch) -> None:
    observed: list[tuple[str, str]] = []
    trained: list[str] = []

    def features(state: object, scenario: str, **kwargs: object) -> torch.Tensor:
        observed.append((scenario, kwargs["cue"]))
        return torch.zeros(kwargs["batch"], 8)

    def training(state: object, cue: str, *args: object) -> tuple[object, float]:
        trained.append(cue)
        return state, 0.0

    monkeypatch.setattr(dataset, "new_fly_state", lambda *args: object())
    monkeypatch.setattr(dataset, "apply_training", training)
    monkeypatch.setattr(dataset, "scenario_features", features)
    data = dataset.generate_dataset(individuals=16, version=version)
    cues = {cue for scenario, cue in observed if scenario in {"liked_odor", "disliked_odor"}}
    expected = {"banana", "apple_vinegar", "yeast", "grape"}
    if version == "toy-v0":
        expected.add("blue_light")
    assert cues == set(trained) == expected
    assert data.features.shape == (16 * len(SCENARIOS) * 4, 8)
    assert set(data.labels.tolist()) == set(range(len(LABELS)))
    train, test = dataset.split_dataset(data)
    fit, validation = dataset.split_dataset(train)
    assert fit.individuals.unique().tolist() == [0, 3, 7, 8, 9, 11, 12, 13, 15]
    assert validation.individuals.unique().tolist() == [1, 2, 14]
    assert test.individuals.unique().tolist() == [4, 5, 6, 10]
