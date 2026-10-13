from __future__ import annotations

from datetime import UTC, datetime, timedelta

from tsuyulabo_api.domain import vial

NOW = datetime(2026, 10, 12, tzinfo=UTC)


def test_meal_uses_placed_cells_and_verified_score() -> None:
    params = {
        "pieces": [{"shape": "o4", "ingredient": "yeast"}, {"shape": "m1", "ingredient": "grape"}]
    }
    food = vial.medium(params, {"moves": [{"p": 0}]}, 1500)
    assert food == {"color": "#cbb789", "moisture": 0.55, "yeast": 1, "nutrition": 0.5}
    assert vial.medium(params, {"moves": []}, 0)["nutrition"] == 0


def test_neglect_is_settled_once_and_cleaning_preserves_rewards() -> None:
    saved = vial.initial(NOW)
    later = NOW + timedelta(hours=24)
    settled = vial.settle(saved, later, 0, 0)
    assert settled["food"]["moisture"] < saved["food"]["moisture"]
    assert settled["mould"] > 0 and settled["grime"] == 1 and settled["pace"] == 0.15
    assert vial.settle(settled, later, 0, 0) == settled
    cleaned = vial.apply(settled, "cleaning", {}, {}, {"score": 100}, later)
    assert cleaned["grime"] == cleaned["mould"] == 0


def test_temperature_and_site_are_from_validated_operations() -> None:
    saved = vial.initial(NOW)
    value = vial.apply(
        saved,
        "temperature",
        {"center_c": 25, "amp_c": 7, "period_ms": 1600, "phase": 0},
        {"stop_ms": 0, "humidity": 0.8},
        {},
        NOW,
    )
    assert value["temperature"] == 25 and value["humidity"] == 0.8
    value = vial.apply(value, "pupation_site", {}, {"choice": "c"}, {}, NOW)
    assert value["pupation_position"][1] == 1.15
