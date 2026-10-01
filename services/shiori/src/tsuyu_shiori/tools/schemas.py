"""Stable, explicit tool arguments shared by every provider."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Cue = Literal["banana", "apple_vinegar", "yeast", "grape", "blue_light"]
Valence = Literal["reward", "punish"]
CUE_DESCRIPTION = (
    "バナナ=banana、りんご酢=apple_vinegar、イースト=yeast、ぶどう=grape、青い光=blue_light"
)
VALENCE_DESCRIPTION = "報酬=reward、罰=punish"


class Arguments(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class CareArguments(Arguments):
    week_id: str
    kinds: list[str] | None = Field(
        default=None,
        description="Record kinds: training, meal, cleaning, temperature, pupation_site, "
        "eclosion, presentation, sleep. Omit for all kinds; [] selects none.",
    )
    research_day: int | None = Field(default=None, ge=1, le=7, description="研究日: 1〜7日目")
    cue: Cue | None = Field(default=None, description=CUE_DESCRIPTION)
    valence: Valence | None = Field(default=None, description=VALENCE_DESCRIPTION)


class AssociationArguments(Arguments):
    fly_id: str
    cue: Cue = Field(description=CUE_DESCRIPTION)


class ExperimentArguments(AssociationArguments):
    trials: int = Field(default=20, ge=1, le=1000)
    seed: int = Field(default=0, ge=0, le=2**32 - 1)


class PaperArguments(Arguments):
    query: str = Field(min_length=1, max_length=1000)
    k: int = Field(default=3, ge=1, le=20)
