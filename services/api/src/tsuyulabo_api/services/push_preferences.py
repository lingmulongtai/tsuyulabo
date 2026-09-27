"""Notification preferences use real JST wall time, independently of dev time travel."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from tsuyulabo_api.domain.push import is_quiet


class PushPreferences(BaseModel):
    model_config = ConfigDict(extra="forbid")

    meal_slots: list[Literal["morning", "noon", "night"]] = Field(
        default_factory=lambda: ["morning", "noon", "night"], max_length=3
    )
    eclosion_night: bool = True
    friend_activity: bool = True
    quiet_start: str = Field(default="23:00", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")
    quiet_end: str = Field(default="07:00", pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")

    def is_quiet(self, now: datetime) -> bool:
        return is_quiet(now, self.quiet_start, self.quiet_end)
