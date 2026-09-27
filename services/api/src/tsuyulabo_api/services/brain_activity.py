"""Bounded process-local activity cache, versioned by the complete brain snapshot."""

from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from threading import Lock
from typing import Any, Literal

from pydantic import BaseModel, Field
from tsuyulabo_api.brain_adapter import BrainAdapter

Scenario = Literal[
    "rest",
    "sugar",
    "bitter",
    "sugar+bitter",
    "looming",
    "light_left",
    "light_right",
    "antenna_touch",
    "liked_odor",
    "disliked_odor",
]


class ActivityGroup(BaseModel):
    name: str
    kind: Literal["sensory", "inter", "output", "modulatory"]
    circuit: str
    rates: list[float] = Field(description="Mean firing rate per neuron in Hz, one per window")


class ActivityEdge(BaseModel):
    pre_group: str
    post_group: str
    weight_sum: float = Field(description="Signed learned wiring sum before individual gains")
    sign: Literal["excitatory", "inhibitory"]


class BrainActivity(BaseModel):
    groups: list[ActivityGroup]
    edges: list[ActivityEdge]
    scenario: Scenario
    duration_ms: float


class ActivityCache:
    def __init__(self, capacity: int = 128) -> None:
        self.capacity = capacity
        self.entries: OrderedDict[tuple[str, str, str, str], BrainActivity] = OrderedDict()
        self.lock = Lock()

    def get(
        self,
        brain: BrainAdapter,
        user_id: str,
        fly_id: str,
        snapshot: dict[str, Any],
        scenario: Scenario,
    ) -> BrainActivity:
        version = hashlib.sha256(json.dumps(snapshot, sort_keys=True).encode()).hexdigest()
        key = (user_id, fly_id, version, scenario)
        # Runs in a worker thread. Serialize misses to bound concurrent CPU work.
        with self.lock:
            if key not in self.entries:
                result = brain.api.activity(brain.restore(snapshot), scenario, seed=0)
                self.entries[key] = BrainActivity.model_validate(result)
                if len(self.entries) > self.capacity:
                    self.entries.popitem(last=False)
            self.entries.move_to_end(key)
            return self.entries[key].model_copy(deep=True)
