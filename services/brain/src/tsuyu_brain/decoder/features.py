"""Output-only temporal features for the measured connectome."""

from __future__ import annotations

import torch
from torch import Tensor

from tsuyu_brain.circuit import SimResult

WINDOWS = 6


def window_rates(result: SimResult, group: str) -> Tensor:
    """Rebin rates into six equal-duration bins, including partial source windows.

    Bins cover the complete trial, so feature width is independent of duration.
    At the evaluation's 300 ms duration these are the original 50 ms windows.
    """
    ends = result.window_ms.cumsum(0)
    starts = ends - result.window_ms
    boundaries = torch.linspace(0, float(ends[-1]), WINDOWS + 1)
    overlap = (
        torch.minimum(ends[:, None], boundaries[None, 1:])
        - torch.maximum(starts[:, None], boundaries[None, :-1])
    ).clamp_min(0)
    return result.rates[group] @ overlap / (boundaries[1:] - boundaries[:-1])


def temporal_features(means: Tensor, windows: Tensor) -> Tensor:
    """Keep eight mean rates, six windows per output, and two signed contrasts."""
    left_right = windows[:, 3] - windows[:, 2]
    approach_avoid = windows[:, 6] - windows[:, 7]
    return torch.cat((means, windows.flatten(1), left_right, approach_avoid), dim=1)
