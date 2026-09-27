"""Shared persistence boundary for API mutations and worker experiments."""

from __future__ import annotations

import base64
from typing import Any

from tsuyulabo_api.brain_adapter import BrainAdapter
from tsuyulabo_api.db.models import Adult, LarvaState


def snapshot(row: Adult | LarvaState) -> dict[str, Any]:
    if row.learned_weights is None:
        return row.brain_snapshot
    return {
        **row.brain_snapshot,
        "params": row.brain_params,
        "state": base64.b64encode(row.learned_weights).decode("ascii"),
    }


def store(row: Adult | LarvaState, state: dict[str, Any], brain: BrainAdapter) -> None:
    row.learned_weights = base64.b64decode(state["state"], validate=True)
    row.brain_params = state["params"]
    row.brain_snapshot = {"training": state["training"]}
    row.preferences = brain.preferences(state)
