from __future__ import annotations

import math

import pytest
import torch
from tsuyu_brain.api import activity, default_params, new_fly_state
from tsuyu_brain.behavior import FEATURES, SCENARIOS, scenario_features
from tsuyu_brain.connectome import load_circuit
from tsuyu_brain.connectome.toy_v0 import CIRCUIT_NAMES


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_activity_shape_determinism_and_no_mutation(scenario: str) -> None:
    state = new_fly_state(default_params(), "toy-v0")
    before = state.kc_mbon.clone()
    wiring = {name: load_circuit(name, "toy-v0").weights.clone() for name in CIRCUIT_NAMES}
    rng = torch.random.get_rng_state().clone()
    result = activity(state, scenario, seed=19)
    assert result == activity(state, scenario, seed=19)
    assert result["duration_ms"] == 300
    assert result["scenario"] == scenario
    assert len(result["groups"]) == 23
    names = {group["name"] for group in result["groups"]}
    assert len(names) == len(result["groups"])
    for group in result["groups"]:
        assert group["circuit"] in CIRCUIT_NAMES
        assert group["kind"] in {"sensory", "inter", "output", "modulatory"}
        assert len(group["rates"]) == 20
        assert all(math.isfinite(rate) and rate >= 0 for rate in group["rates"])
    for edge in result["edges"]:
        assert {edge["pre_group"], edge["post_group"]} <= names
        assert (edge["weight_sum"] > 0) == (edge["sign"] == "excitatory")
    assert torch.equal(state.kc_mbon, before)
    assert torch.equal(torch.random.get_rng_state(), rng)
    assert all(
        torch.equal(load_circuit(name, "toy-v0").weights, value) for name, value in wiring.items()
    )
    features = scenario_features(state, scenario, seed=19)[0]
    for group in result["groups"]:
        if group["name"] in FEATURES:
            assert sum(group["rates"]) / 20 == pytest.approx(
                float(features[FEATURES.index(group["name"])]), rel=1e-6, abs=1e-5
            )


def test_activity_uses_learned_weights_and_custom_windows() -> None:
    state = new_fly_state(default_params(), "toy-v0")
    state.kc_mbon[:, 1] = 0
    result = activity(state, "liked_odor", seed=0, windows=7)
    assert all(len(group["rates"]) == 7 for group in result["groups"])
    assert result["duration_ms"] == 297.5
    assert not any(edge["post_group"] == "MBON_av" for edge in result["edges"])
    assert all(
        group["kind"] == "modulatory"
        for group in result["groups"]
        if group["name"] in {"PAM", "PPL1"}
    )


@pytest.mark.parametrize("windows", [0, -1, 101, 2.5, True])
def test_invalid_windows(windows: int) -> None:
    with pytest.raises(ValueError, match="windows"):
        activity(new_fly_state(default_params(), "toy-v0"), "sugar", seed=0, windows=windows)


def test_invalid_scenario() -> None:
    with pytest.raises(ValueError, match="scenario"):
        activity(new_fly_state(default_params(), "toy-v0"), "unknown", seed=0)


@pytest.mark.parametrize("version", ["toy-v0", "malecns-v1.0"])
def test_viewer_uses_state_version_with_stable_palette(version: str) -> None:
    from tsuyu_brain.circuit import simulate

    state = new_fly_state(default_params(), version)
    result = activity(state, "sugar", seed=19)
    assert len(result["groups"]) == 23
    mn9 = next(group for group in result["groups"] if group["name"] == "MN9")
    expected = simulate(
        load_circuit("feeding", version), {"Gr64f": 1}, state.params, seed=19, window_ms=15
    ).rates["MN9"][0]
    assert mn9["rates"] == expected.tolist()
