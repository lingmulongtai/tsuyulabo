"""Worker exports for the shared API/Shiori brain boundary and test double."""

from __future__ import annotations

from copy import deepcopy

from tsuyulabo_api.services.shiori_brain import (
    BrainEngine as BrainEngine,
)
from tsuyulabo_api.services.shiori_brain import (
    BrainSnapshot as BrainSnapshot,
)
from tsuyulabo_api.services.shiori_brain import (
    BrainUnavailable as BrainUnavailable,
)
from tsuyulabo_api.services.shiori_brain import (
    RealBrainEngine as RealBrainEngine,
)


class FakeBrainEngine:
    """Explicit test double with deterministic counts and no brain imports."""

    def run_odor_choice(
        self, snapshot: BrainSnapshot, cue: str, trials: int, seed: int
    ) -> dict[str, int]:
        copied = deepcopy(snapshot)
        value = copied.params.get("associations", {}).get(cue, 0.0)
        for training in copied.training:
            if training.get("cue") == cue:
                value += training.get("learning_strength", training.get("strength", 0.1)) * (
                    1 if training["valence"] == "reward" else -1
                )
        toward = round(trials * (max(-1.0, min(1.0, value)) + 1) / 2)
        return {"toward": toward, "away": trials - toward}
