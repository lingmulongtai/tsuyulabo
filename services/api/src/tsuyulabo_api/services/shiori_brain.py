"""Copy-only experiment boundary shared by inline Shiori and the queue worker."""

from __future__ import annotations

from dataclasses import dataclass, field
from importlib import import_module
from typing import Any, Protocol


@dataclass(frozen=True)
class BrainSnapshot:
    fly_id: str
    params: dict[str, Any] = field(default_factory=dict)
    learned_weights: bytes | None = None
    training: list[dict[str, Any]] = field(default_factory=list)
    traits: list[str] = field(default_factory=list)
    sex: str = "f"
    legacy_snapshot: dict[str, Any] = field(default_factory=dict)


class BrainEngine(Protocol):
    def run_odor_choice(
        self, snapshot: BrainSnapshot, cue: str, trials: int, seed: int
    ) -> dict[str, int]: ...


class BrainUnavailable(RuntimeError):
    pass


class RealBrainEngine:
    """Read the same public byte codec as the API; never replay persisted weights."""

    def run_odor_choice(
        self, snapshot: BrainSnapshot, cue: str, trials: int, seed: int
    ) -> dict[str, int]:
        try:
            api = import_module("tsuyu_brain.api")
        except ModuleNotFoundError as exc:
            raise BrainUnavailable("tsuyu_brain.api is not installed") from exc
        if snapshot.learned_weights is not None:
            state = api.FlyState.from_bytes(snapshot.learned_weights)
        elif snapshot.legacy_snapshot:
            from tsuyulabo_api.brain_adapter import BrainAdapter

            state = BrainAdapter().restore(snapshot.legacy_snapshot)
        else:
            raise BrainUnavailable("brain state is missing; run the API brain backfill")
        result = api.run_odor_choice(state, cue, trials, seed)
        return {"toward": int(result["toward"]), "away": int(result["away"])}
