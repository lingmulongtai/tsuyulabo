"""Circuit description and batched simulation with rates in Hz."""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field

import torch
from torch import Tensor

from tsuyu_brain.neuron import DT_MS, LIFPopulation
from tsuyu_brain.params import BrainParams


@dataclass(frozen=True)
class Circuit:
    """Weights use [source, target] orientation and include their signs.

    Treat registry circuits as read-only. Use with_weights for private changes.
    Input groups are clamped Poisson sources; other groups are LIF neurons.
    """

    name: str
    groups: dict[str, slice]
    weights: Tensor
    signs: Tensor
    input_groups: tuple[str, ...]
    output_groups: tuple[str, ...]
    version: str = "toy-v0"
    projections: tuple[tuple[str, str], ...] = ()
    tonic: dict[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        n = self.weights.shape[0]
        if self.weights.shape != (n, n) or self.signs.shape != (n,):
            raise ValueError("inconsistent circuit dimensions")
        indices = [i for group in self.groups.values() for i in range(group.start, group.stop)]
        if sorted(indices) != list(range(n)):
            raise ValueError("groups must partition neurons")
        if not set(self.input_groups + self.output_groups) <= self.groups.keys():
            raise ValueError("unknown input or output group")
        if not torch.isfinite(self.weights).all():
            raise ValueError("weights must be finite")
        if not ((self.signs == 1) | (self.signs == -1)).all():
            raise ValueError("signs must be excitatory (+1) or inhibitory (-1)")
        if (self.weights * self.signs[:, None] < 0).any():
            raise ValueError("outgoing weights disagree with neuron signs")

    def with_weights(self, weights: Tensor) -> Circuit:
        from dataclasses import replace

        return replace(self, weights=weights.clone())


@dataclass(frozen=True)
class SimResult:
    rates: dict[str, Tensor]  # [batch, window], Hz averaged across each group
    neuron_rates: Tensor  # [batch, neuron], Hz over the complete duration
    window_ms: Tensor  # actual duration, including a partial final window
    spikes: Tensor | None = None  # [time, batch, neuron]


def simulate(
    circuit: Circuit,
    stimulus: Mapping[str, float | Tensor],
    params: BrainParams,
    duration_ms: float = 300.0,
    batch: int = 1,
    seed: int = 0,
    *,
    window_ms: float = 50.0,
    record_spikes: bool = False,
) -> SimResult:
    """Stimulus values scale params.input_rate_hz; tensors broadcast to [batch, group]."""
    for value in (duration_ms, window_ms):
        if (
            not math.isfinite(value)
            or value <= 0
            or not math.isclose(value / DT_MS, round(value / DT_MS))
        ):
            raise ValueError("duration and windows must be positive multiples of dt")
    if batch < 1 or set(stimulus) - set(circuit.input_groups):
        raise ValueError("invalid batch or unknown stimulus group")
    n = circuit.weights.shape[0]
    weights = circuit.weights.clone() * (params.input_current / 6.0)
    thresholds = torch.full((n,), params.threshold)
    tonic = torch.zeros(n)
    gain_names = {
        "ORN": "orn",
        "PN": "pn",
        "KC": "kc",
        "visual": "visual",
        "Gr64f": "sugar",
        "Gr66a": "bitter",
        "MN9": "feeding",
        "DNp01": "escape",
        "walking_DN": "light",
        "aDN": "grooming",
        "MBON_ap": "mbon",
        "MBON_av": "mbon",
    }
    threshold_names = {
        "KC": "kc",
        "MN9": "feeding",
        "DNp01": "escape",
        "DNa02_L": "steering",
        "DNa02_R": "steering",
        "aDN": "grooming",
        "MBON_ap": "mbon",
        "MBON_av": "mbon",
    }
    for name, group in circuit.groups.items():
        if name in gain_names:
            weights[:, group] *= getattr(params, gain_names[name] + "_gain")
        if name in threshold_names:
            thresholds[group] *= getattr(params, threshold_names[name] + "_threshold")
        tonic[group] = circuit.tonic.get(name, 0.0)
    for name, direction in (("DNa02_L", -1), ("DNa02_R", 1)):
        if name in circuit.groups:
            weights[:, circuit.groups[name]] *= 1 + direction * params.turn_asymmetry
    if "walking_DN" in circuit.groups:
        tonic[circuit.groups["walking_DN"]] += params.walking_current * params.walking_gain
    rates = torch.zeros(batch, n)
    input_mask = torch.zeros(n, dtype=torch.bool)
    for name in circuit.input_groups:
        group = circuit.groups[name]
        input_mask[group] = True
        gain = getattr(params, gain_names.get(name, "") + "_gain", 1.0)
        rates[:, group] = torch.as_tensor(stimulus.get(name, 0.0)) * params.input_rate_hz * gain
    if not torch.isfinite(rates).all() or (rates < 0).any():
        raise ValueError("stimulus must be finite and nonnegative")
    steps, window_steps = round(duration_ms / DT_MS), round(window_ms / DT_MS)
    generator = torch.Generator().manual_seed(seed)
    # Generate only sensory random draws; never alter the process-global RNG.
    probabilities = -torch.expm1(-rates[:, input_mask] * DT_MS / 1000)
    inputs = torch.rand((steps, batch, int(input_mask.sum())), generator=generator) < probabilities
    population = LIFPopulation(n, batch, thresholds)
    previous = torch.zeros(batch, n)
    counts = torch.zeros(batch, n)
    window_counts = torch.zeros_like(counts)
    group_windows: dict[str, list[Tensor]] = {name: [] for name in circuit.groups}
    windows: list[float] = []
    raster: list[Tensor] = []
    # Sparse multiplication avoids costly threaded dense operations for tiny networks.
    operator = weights.T.to_sparse().coalesce()
    with torch.no_grad():
        for step in range(steps):
            impulses = torch.sparse.mm(operator, previous.T).T
            spikes = population.step(impulses, tonic)
            spikes[:, input_mask] = inputs[step]
            previous = spikes.float()
            counts += previous
            window_counts += previous
            if record_spikes:
                raster.append(spikes.clone())
            if (step + 1) % window_steps == 0 or step + 1 == steps:
                elapsed = ((step % window_steps) + 1) * DT_MS
                windows.append(elapsed)
                for name, group in circuit.groups.items():
                    group_windows[name].append(window_counts[:, group].mean(1) * 1000 / elapsed)
                window_counts.zero_()
    return SimResult(
        {name: torch.stack(values, dim=1) for name, values in group_windows.items()},
        counts * 1000 / duration_ms,
        torch.tensor(windows),
        torch.stack(raster) if record_spikes else None,
    )
