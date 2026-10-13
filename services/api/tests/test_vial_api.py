from __future__ import annotations

from typing import Any
from uuid import uuid4

from tsuyulabo_api.routers import home, puzzles, weeks

from .game_support import GameClient


async def test_vial_care_persists_and_replay_is_identical(sessions: Any) -> None:
    async with GameClient(sessions, weeks.router, puzzles.router, home.router) as game:
        week = (await game.post("/v1/weeks")).json()
        assert week["vial"]["food"]["moisture"] == 0.7
        issued = (await game.post("/v1/puzzles", {"kind": "meal"})).json()
        path = f"/v1/puzzles/{issued['puzzle_id']}/submit"
        bad = await game.post(path, {"moves": [{"p": 99, "r": 0, "c": 0, "t": 0}], "elapsed_ms": 0})
        assert bad.status_code == 422
        assert (await game.get("/v1/home")).json()["vial"] == week["vial"]
        body = {
            "moves": [{"p": 0, "r": 0, "c": 0, "t": 0}],
            "elapsed_ms": 0,
            "vial": {"food": {"nutrition": 100}},
        }
        key = str(uuid4())
        response = await game.post(path, body, key)
        assert response.status_code == 200, response.text
        result = response.json()
        assert 0 < result["vial"]["food"]["nutrition"] <= 1
        assert (await game.post(path, body, key)).json() == result
        assert (await game.get("/v1/home")).json()["vial"]["food"] == result["vial"]["food"]
        await game.advance(to="next_day")
        neglected = (await game.get("/v1/home")).json()["vial"]
        assert neglected["food"]["moisture"] < result["vial"]["food"]["moisture"]
        assert neglected["mould"] > 0 and neglected["pace"] < result["vial"]["pace"]


async def test_temperature_humidity_and_wipe_submission(sessions: Any) -> None:
    async with GameClient(sessions, weeks.router, puzzles.router, home.router) as game:
        await game.post("/v1/weeks")
        issued = (await game.post("/v1/puzzles", {"kind": "temperature"})).json()
        path = f"/v1/puzzles/{issued['puzzle_id']}/submit"
        assert (
            await game.post(path, {"stop_ms": 0, "elapsed_ms": 0, "humidity": 2})
        ).status_code == 422
        result = await game.post(path, {"stop_ms": 0, "elapsed_ms": 0, "humidity": 0.8})
        assert result.status_code == 200 and result.json()["vial"]["humidity"] == 0.8
        await game.advance(to="next_day")
        issued = (await game.post("/v1/puzzles", {"kind": "cleaning"})).json()
        assert issued["params"]["interaction"] == "wipe"
        stamps = [
            {"u": (col + 0.5) / 6, "v": (row + 0.5) / 9, "t": (row * 6 + col) * 40}
            for row in range(9)
            for col in range(6)
        ]
        game.clock.advance(3)
        result = await game.post(
            f"/v1/puzzles/{issued['puzzle_id']}/submit", {"strokes": stamps, "elapsed_ms": 2200}
        )
        assert result.status_code == 200, result.text
        assert result.json()["score"] == 100
        assert result.json()["vial"]["grime"] == result.json()["vial"]["mould"] == 0


async def test_missed_pupation_uses_the_default_site_in_the_vial(sessions: Any) -> None:
    async with GameClient(sessions, weeks.router, puzzles.router, home.router) as game:
        await game.post("/v1/weeks")
        for _ in range(4):
            await game.advance(to="next_day")
        await game.advance(to="next_slot")
        await game.advance(to="next_slot")
        issued = (await game.post("/v1/puzzles", {"kind": "pupation_site"})).json()
        # Existing missed-care rule selects the middle public option.
        expected = issued["params"]["options"][1]["position"]
        await game.advance(to="next_day")
        assert (await game.get("/v1/home")).json()["vial"]["pupation_position"] == expected
