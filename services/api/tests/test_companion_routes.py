from __future__ import annotations

from tsuyulabo_api.routers import brain, shiori, weeks

from .game_support import GameClient


async def test_companion_owns_diary_hint_and_current_why(sessions):
    async with GameClient(sessions, brain.router, shiori.router, weeks.router) as game:
        fly_id = (await game.post("/v1/weeks", {})).json()["id"]
        assert (await game.get("/v1/shiori/individuals")).json()[0]["id"] == fly_id
        assert (await game.get(f"/v1/shiori/diary?fly_id={fly_id}")).json() == []
        assert (await game.get(f"/v1/shiori/flies/{fly_id}/hint")).json() is None
        assert (await game.post(f"/v1/shiori/flies/{fly_id}/why", {})).status_code == 409
        await game.get(f"/v1/flies/{fly_id}/behavior")
        response = await game.post(f"/v1/shiori/flies/{fly_id}/why", {"behaviour": "walk"})
        assert response.status_code == 200
        assert "歩く" in response.json()["text"]
        assert response.json()["evidence"] == ["#0001"]
        assert response.json()["text"].count("。") == 2
        assert (
            await game.post(f"/v1/shiori/flies/{fly_id}/why", {"behaviour": "feed"})
        ).status_code == 409
        async with GameClient(sessions, shiori.router) as other:
            assert (await other.get(f"/v1/shiori/diary?fly_id={fly_id}")).status_code == 404
            assert (await other.get(f"/v1/shiori/flies/{fly_id}/hint")).status_code == 404
            assert (await other.post(f"/v1/shiori/flies/{fly_id}/why", {})).status_code == 404
            assert (await other.post("/v1/shiori/hints/unknown/dismiss", {})).status_code == 404
        game.clock.advance(121)
        assert (await game.post(f"/v1/shiori/flies/{fly_id}/why", {})).status_code == 409
