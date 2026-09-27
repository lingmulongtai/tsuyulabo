"""Response envelopes expose the derived circadian contract in OpenAPI."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class CircadianResponse(BaseModel):
    gauge: int = Field(ge=0, le=100)
    streak: int = Field(ge=0, le=7)
    typical_bedtime: str | None
    typical_wake: str | None


class HomeResponse(BaseModel):
    clock: dict[str, Any]
    week: dict[str, Any] | None
    fly: dict[str, Any] | None
    todo: list[dict[str, Any]]
    balances: dict[str, int]
    team: dict[str, Any]
    shiori: dict[str, Any]
    circadian: CircadianResponse


class SleepEndResponse(BaseModel):
    id: str
    hours: float
    bonus: int
    energy_recovered: dict[str, float]
    circadian: CircadianResponse
