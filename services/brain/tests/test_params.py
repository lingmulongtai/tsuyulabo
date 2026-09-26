from __future__ import annotations

import pytest
from tsuyu_brain.params import BrainParams, default_params


def test_json_round_trip() -> None:
    params = default_params()
    assert BrainParams.from_json(params.to_json()) == params
    assert len(params.to_dict()) == 24


@pytest.mark.parametrize(
    "values", [{"threshold": 0}, {"orn_gain": float("nan")}, {"turn_asymmetry": 1}]
)
def test_invalid_params(values: dict[str, float]) -> None:
    with pytest.raises(ValueError):
        BrainParams(**values)
