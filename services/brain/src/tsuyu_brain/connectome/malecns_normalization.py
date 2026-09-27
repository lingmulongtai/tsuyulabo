"""Offline homeostasis for the sampled mushroom body; never create an edge."""

from __future__ import annotations

import math

import torch
from torch import Tensor

from tsuyu_brain.circuit import Circuit


def normalize_mbon_inputs(
    circuit: Circuit, reference_rates: Tensor, kc_budget: float = 40.0
) -> tuple[Circuit, dict[str, object]]:
    """Equalize KC input totals and correct APL's reference firing-rate imbalance.

    Each MBON receives the same total KC magnitude, preserving its afferent ratios.
    APL feedback into both valence pools uses the same population-rate correction.
    Reference rates must come from an untrained, independent calibration trial.
    """
    if not math.isfinite(kc_budget) or kc_budget <= 0:
        raise ValueError("KC budget must be finite and positive")
    if reference_rates.shape != circuit.signs.shape:
        raise ValueError("reference rates must match the circuit")
    if not torch.isfinite(reference_rates).all() or (reference_rates < 0).any():
        raise ValueError("reference rates must be finite and nonnegative")
    kc, apl = circuit.groups["KC"], circuit.groups["APL"]
    kc_rate = float(reference_rates[kc].mean()) if kc.stop > kc.start else 0.0
    apl_rate = float(reference_rates[apl].mean()) if apl.stop > apl.start else 0.0
    # Missing/silent reference populations cannot justify a feedback correction.
    feedback = min(1.0, kc_rate / apl_rate) if kc_rate > 0 and apl_rate > 0 else 1.0
    weights = circuit.weights.clone()
    factors = {}
    for group in ("MBON_ap", "MBON_av"):
        target = circuit.groups[group]
        totals = weights[kc, target].abs().sum(0)
        gains = torch.where(totals > 0, kc_budget / totals.clamp_min(1e-12), 1.0)
        weights[kc, target] *= gains
        weights[apl, target] *= feedback
        factors[f"KC->{group}"] = gains.tolist()
        factors[f"APL->{group}"] = [feedback] * (target.stop - target.start)
    return circuit.with_weights(weights), {
        "method": "equal KC magnitude per MBON; common APL gain = min(1, mean KC Hz / mean APL Hz)",
        "reason": "sampled KC drive and nearly saturated APL feedback silence avoidance MBONs",
        "kc_budget": kc_budget,
        "kc_budget_reason": "40 is closest to neutral untrained PI in the seed-19 "
        "sweep of 20, 40, 60, 80, 100, 120; independent evaluation uses seed 71",
        "reference_kc_hz": kc_rate,
        "reference_apl_hz": apl_rate,
        "projection_factors": factors,
    }
