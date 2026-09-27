"""Copy-only, group-level activity for the brain viewer (synthetic toy-v0 wiring)."""

from __future__ import annotations

from typing import Literal, TypedDict

from tsuyu_brain.behavior import scenario_inputs
from tsuyu_brain.circuit import simulate
from tsuyu_brain.connectome import load_circuit
from tsuyu_brain.connectome.toy_v0 import CIRCUIT_NAMES
from tsuyu_brain.learning import FlyState, learned_circuit
from tsuyu_brain.neuron import DT_MS


class ActivityGroup(TypedDict):
    name: str
    kind: Literal["sensory", "inter", "output", "modulatory"]
    circuit: str
    rates: list[float]


class ActivityEdge(TypedDict):
    pre_group: str
    post_group: str
    weight_sum: float
    sign: Literal["excitatory", "inhibitory"]


class Activity(TypedDict):
    groups: list[ActivityGroup]
    edges: list[ActivityEdge]
    scenario: str
    duration_ms: float


def activity(state: FlyState, scenario: str, seed: int, windows: int = 20) -> Activity:
    """Run up to 300 ms, in equal windows aligned to the 0.5 ms simulation step.

    Inactive toy circuits have no spontaneous drive, so their rates are zero.
    Steering always runs to retain spontaneous walking-DN firing. Odor scenarios
    both present banana, like behavior(); learned weights determine preference.
    DANs only fire during training, which this read-only observation never applies.
    Edge sums are signed learned wiring weights, before individual gain scaling.
    """
    if type(windows) is not int or not 1 <= windows <= 100:
        raise ValueError("windows must be an integer in [1, 100]")
    params, jobs = scenario_inputs(state, scenario)
    window_ms = (600 // windows) * DT_MS
    duration_ms = windows * window_ms
    groups: list[ActivityGroup] = []
    edges: list[ActivityEdge] = []
    for name in CIRCUIT_NAMES:
        circuit = learned_circuit(state) if name == "olfaction_mb" else load_circuit(name)
        result = (
            simulate(circuit, jobs[name], params, duration_ms, seed=seed, window_ms=window_ms)
            if name in jobs
            else None
        )
        for group in circuit.groups:
            kind: Literal["sensory", "inter", "output", "modulatory"] = "inter"
            if group in {"PAM", "PPL1"}:
                kind = "modulatory"
            elif group in circuit.input_groups:
                kind = "sensory"
            elif group in circuit.output_groups:
                kind = "output"
            groups.append(
                {
                    "name": group,
                    "kind": kind,
                    "circuit": name,
                    "rates": result.rates[group][0].tolist() if result else [0.0] * windows,
                }
            )
        for pre, post in circuit.projections:
            weight = float(circuit.weights[circuit.groups[pre], circuit.groups[post]].sum())
            if weight:
                edges.append(
                    {
                        "pre_group": pre,
                        "post_group": post,
                        "weight_sum": weight,
                        "sign": "excitatory" if weight > 0 else "inhibitory",
                    }
                )
    return {"groups": groups, "edges": edges, "scenario": scenario, "duration_ms": duration_ms}
