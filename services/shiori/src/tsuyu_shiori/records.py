"""Host-owned records. This module deliberately knows nothing about database models."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol


@dataclass(frozen=True)
class Record:
    id: str
    kind: str
    data: dict[str, Any] = field(default_factory=dict)
    week_id: str | None = None
    fly_id: str | None = None
    occurred_at: datetime | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "kind": self.kind,
            "data": deepcopy(self.data),
            "week_id": self.week_id,
            "fly_id": self.fly_id,
            "occurred_at": self.occurred_at.isoformat() if self.occurred_at else None,
        }


class RecordStore(Protocol):
    """Every implementation must scope reads and ID checks to the current user."""

    async def care_events(self, week_id: str, kinds: list[str] | None = None) -> list[Record]: ...

    async def sleep_sessions(self, week_id: str) -> list[Record]: ...

    async def association(self, fly_id: str, cue: str) -> Record | None: ...

    async def experiment(self, evidence_id: str) -> Record | None: ...

    async def exists(self, evidence_id: str) -> bool: ...


class Lab(Protocol):
    async def run_odor_choice(
        self, fly_id: str, cue: str, trials: int = 20, seed: int = 0
    ) -> Record:
        """Run on a private brain copy, persist the result, then return its evidence ID."""
        ...


class MemoryRecordStore:
    def __init__(self, records: list[Record] | None = None) -> None:
        self.records = {record.id: deepcopy(record) for record in records or []}

    def add(self, record: Record) -> None:
        self.records[record.id] = deepcopy(record)

    async def care_events(self, week_id: str, kinds: list[str] | None = None) -> list[Record]:
        return deepcopy(
            [
                r
                for r in self.records.values()
                if r.week_id == week_id
                and r.kind not in {"sleep", "experiment", "association"}
                and (kinds is None or r.kind in kinds)
            ]
        )

    async def sleep_sessions(self, week_id: str) -> list[Record]:
        return deepcopy(
            [r for r in self.records.values() if r.week_id == week_id and r.kind == "sleep"]
        )

    async def association(self, fly_id: str, cue: str) -> Record | None:
        matches = [
            r
            for r in self.records.values()
            if r.fly_id == fly_id
            and r.data.get("cue") == cue
            and r.kind in {"association", "training"}
            and "value" in r.data
        ]
        return deepcopy(matches[-1]) if matches else None

    async def experiment(self, evidence_id: str) -> Record | None:
        record = self.records.get(evidence_id)
        return deepcopy(record) if record and record.kind == "experiment" else None

    async def exists(self, evidence_id: str) -> bool:
        return evidence_id in self.records


class MemoryLab:
    """An explicit deterministic fake, never a fallback for a missing real engine."""

    def __init__(self, store: MemoryRecordStore, states: dict[str, dict[str, float]]) -> None:
        self.store, self.states = store, deepcopy(states)

    async def run_odor_choice(
        self, fly_id: str, cue: str, trials: int = 20, seed: int = 0
    ) -> Record:
        if not 1 <= trials <= 1000:
            raise ValueError("trials must be between 1 and 1000")
        state = deepcopy(self.states[fly_id])
        value = max(-1.0, min(1.0, state.get(cue, 0.0)))
        toward = round(trials * (value + 1) / 2)
        seq = 1
        while await self.store.exists(f"#c-{seq}"):
            seq += 1
        record = Record(
            f"#c-{seq}",
            "experiment",
            {
                "cue": cue,
                "trials": trials,
                "seed": seed,
                "toward": toward,
                "away": trials - toward,
                "model": "deterministic-fake",
            },
            fly_id=fly_id,
        )
        self.store.add(record)
        return record
