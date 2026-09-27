"""The same frozen-input simulation is used by inline and queued jobs."""

from __future__ import annotations

import asyncio
from typing import Any

from tsuyulabo_api.brain_adapter import BrainAdapter
from tsuyulabo_api.domain.maze import run
from tsuyulabo_api.services.jobs import JobFunction


def simulate(params: dict[str, Any]) -> dict[str, Any]:
    brain = BrainAdapter()
    state = brain.restore(params["snapshot"])
    return run(
        params["maze"],
        params["placements"],
        params["seed"],
        lambda observation: brain.api.maze_policy(state, observation),
    )


def handler() -> JobFunction:
    async def perform(params: dict[str, Any]) -> dict[str, Any]:
        return await asyncio.to_thread(simulate, params)

    return perform
