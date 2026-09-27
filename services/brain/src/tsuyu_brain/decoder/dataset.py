"""Generate labeled simulation data with splits grouped by individual."""

from __future__ import annotations

from dataclasses import dataclass

import torch
from torch import Tensor

from tsuyu_brain.behavior import LABELS, SCENARIOS, scenario_features
from tsuyu_brain.connectome.stimuli import CUE_GLOMERULI
from tsuyu_brain.connectome.toy_v0 import CUES
from tsuyu_brain.individuality import TRAIT_EFFECTS, generate_individual
from tsuyu_brain.learning import apply_training, new_fly_state


@dataclass(frozen=True)
class Dataset:
    features: Tensor
    labels: Tensor
    individuals: Tensor


def generate_dataset(
    individuals: int = 16,
    trials: int = 4,
    seed: int = 123,
    *,
    shuffle_seed: int | None = None,
    version: str = "toy-v0",
) -> Dataset:
    if individuals < 2 or trials < 1:
        raise ValueError("at least two individuals and one trial required")
    features, labels, ids = [], [], []
    traits = (None, *TRAIT_EFFECTS)
    # MaleCNS has no complete visual-to-KC path. A blue-light trial cannot
    # truthfully be labeled as a liked/disliked odor; retain all four odors.
    cues = tuple(CUE_GLOMERULI) if version == "malecns-v1.0" else CUES
    for individual in range(individuals):
        individual_seed = seed + 1009 * individual
        trait = traits[individual % len(traits)]
        params = generate_individual(
            [] if trait is None else [trait], "m" if individual % 2 else "f", individual_seed
        )
        original = new_fly_state(params, version)
        cue = cues[individual % len(cues)]
        for index, (scenario, label) in enumerate(SCENARIOS.items()):
            state = original
            if scenario in {"liked_odor", "disliked_odor"}:
                valence = "reward" if scenario == "liked_odor" else "punish"
                for repetition in range(3):
                    state, _ = apply_training(state, cue, valence, 1, individual_seed + repetition)
            x = scenario_features(
                state,
                scenario,
                cue=cue,
                batch=trials,
                intensity=0.85 + 0.1 * (individual % 4),
                seed=individual_seed + index,
                shuffle_seed=shuffle_seed,
            )
            features.append(x)
            labels.extend([LABELS.index(label)] * trials)
            ids.extend([individual] * trials)
    return Dataset(torch.cat(features), torch.tensor(labels), torch.tensor(ids))


def split_dataset(data: Dataset, seed: int = 7, fraction: float = 0.75) -> tuple[Dataset, Dataset]:
    if not 0 < fraction < 1:
        raise ValueError("split fraction must be between zero and one")
    ids = data.individuals.unique()
    if len(ids) < 2:
        raise ValueError("at least two individuals required for a held-out split")
    ids = ids[torch.randperm(len(ids), generator=torch.Generator().manual_seed(seed))]
    count = max(1, min(len(ids) - 1, int(len(ids) * fraction)))
    mask = torch.isin(data.individuals, ids[:count])
    return tuple(
        Dataset(data.features[selection], data.labels[selection], data.individuals[selection])
        for selection in (mask, ~mask)
    )
