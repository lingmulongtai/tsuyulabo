from __future__ import annotations

from copy import deepcopy
from typing import Any
from unittest.mock import patch

import pytest
from tsuyu_brain import api
from tsuyulabo_api.brain_adapter import BrainAdapter
from tsuyulabo_api.db.models import Adult, Week
from tsuyulabo_api.routers import brain, weeks
from tsuyulabo_api.services.brain_activity import ActivityCache

from .adult_fixtures import make_adult
from .game_support import GameClient


async def test_activity_route_cache_versions_and_ownership(sessions: Any) -> None:
    async with GameClient(sessions, brain.router, weeks.router) as game:
        game.app.state.brain_adapter = BrainAdapter()
        adult_id = await make_adult(sessions, game)
        path = f"/v1/flies/{adult_id}/brain/activity"
        async with sessions() as session:
            adult = await session.get(Adult, adult_id)
            before = (adult.learned_weights, deepcopy(adult.brain_params), adult.brain_snapshot)
        with patch.object(api, "activity", wraps=api.activity) as compute:
            first = await game.get(path)
            assert first.status_code == 200, first.text
            data = first.json()
            assert data["scenario"] == "sugar"
            assert data["duration_ms"] == 300
            assert len(data["groups"]) == 23
            assert all(len(group["rates"]) == 20 for group in data["groups"])
            assert (await game.get(path)).json() == data
            assert compute.call_count == 1
            assert (await game.get(path + "?scenario=looming")).status_code == 200
            assert compute.call_count == 2
            async with sessions() as session, session.begin():
                adult = await session.get(Adult, adult_id)
                assert (adult.learned_weights, adult.brain_params, adult.brain_snapshot) == before
                state = api.FlyState.from_bytes(adult.learned_weights)
                state.kc_mbon[:, 1] = 0
                adult.learned_weights = state.to_bytes()
            updated = (await game.get(path)).json()
            assert updated["edges"] != data["edges"]
            assert compute.call_count == 3
            async with GameClient(sessions, brain.router) as other:
                assert (await other.get(path)).status_code == 404
            assert compute.call_count == 3
        assert (await game.client.get(path)).status_code == 401
        assert (await game.get(path + "?scenario=invalid")).status_code == 422
        assert (await game.get("/v1/flies/missing/brain/activity")).status_code == 404
        week_id = (await game.post("/v1/weeks")).json()["id"]
        larva_path = f"/v1/flies/{week_id}/brain/activity?scenario=rest"
        assert (await game.get(larva_path)).status_code == 200
        async with sessions() as session, session.begin():
            week = await session.get(Week, week_id)
            week.status = "eclosed"
        assert (await game.get(larva_path)).status_code == 404
        schema = game.app.openapi()
        operation = schema["paths"]["/v1/flies/{fly_id}/brain/activity"]["get"]
        assert operation["responses"]["200"]["content"]["application/json"]["schema"] == {
            "$ref": "#/components/schemas/BrainActivity"
        }


def test_activity_cache_eviction_and_defensive_copy() -> None:
    cache = ActivityCache(capacity=1)
    adapter = BrainAdapter()
    snapshot = adapter.new()
    with patch.object(api, "activity", wraps=api.activity) as compute:
        first = cache.get(adapter, "user", "fly", snapshot, "rest")
        first.groups.clear()
        assert cache.get(adapter, "user", "fly", snapshot, "rest").groups
        assert compute.call_count == 1
        cache.get(adapter, "user", "fly", snapshot, "sugar")
        cache.get(adapter, "user", "fly", snapshot, "rest")
        assert compute.call_count == 3
        assert len(cache.entries) == 1


@pytest.mark.parametrize("scenario", ["liked_odor", "disliked_odor", "light_left", "bitter"])
def test_activity_schema_accepts_engine_results(scenario: str) -> None:
    from tsuyulabo_api.services.brain_activity import BrainActivity

    result = api.activity(api.new_fly_state(api.default_params()), scenario, seed=0)
    assert BrainActivity.model_validate(result).scenario == scenario
