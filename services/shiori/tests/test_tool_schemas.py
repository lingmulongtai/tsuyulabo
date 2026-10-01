from __future__ import annotations

import pytest
from tsuyu_shiori.tools.schemas import AssociationArguments, CareArguments


def test_enum_schema_contains_japanese_mapping() -> None:
    for model in (AssociationArguments, CareArguments):
        cue = model.model_json_schema()["properties"]["cue"]
        assert "イースト=yeast" in cue["description"]
        assert "blue_light" in str(cue)
    valence = CareArguments.model_json_schema()["properties"]["valence"]
    assert "報酬=reward" in valence["description"] and "punish" in str(valence)


@pytest.mark.parametrize(
    "arguments",
    [
        {"cue": "バナナ"},
        {"valence": "penalty"},
        {"research_day": True},
        {"research_day": 8},
        {"research_day": "2"},
    ],
)
def test_invalid_filters_are_rejected(arguments: dict) -> None:
    with pytest.raises(ValueError):
        CareArguments.model_validate({"week_id": "w", **arguments})
