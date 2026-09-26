"""Storage-independent input records; timestamps refer to the explicit game clock."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class CareEvent:
    at: datetime
    kind: str
    score: int = 0
    stars: int = 0
    great_success: bool = False
    hirameki: bool = False
    hit: bool = False
