from __future__ import annotations

from typing import Any
from uuid import uuid4

import pytest
from tsuyulabo_api.routers import adults

from .adult_fixtures import make_adult
from .game_support import GameClient


async def test_rename_persists_and_replays_without_overwriting_later_name(sessions: Any) -> None:
    async with GameClient(sessions, adults.router) as game:
        adult_id = await make_adult(sessions, game)
        path = f"/v1/adults/{adult_id}"
        before = (await game.get(path)).json()
        headers = game.headers | {"Idempotency-Key": str(uuid4())}
        first = await game.client.patch(path, json={"name": "　しずく  "}, headers=headers)
        assert first.status_code == 200
        assert first.json() == before | {"name": "しずく"}
        later = await game.client.patch(
            path,
            json={"name": "あ" * 12},
            headers=game.headers | {"Idempotency-Key": str(uuid4())},
        )
        assert later.status_code == 200
        conflict = await game.client.patch(path, json={"name": "みつ"}, headers=headers)
        assert conflict.status_code == 409
        assert conflict.json()["error"]["code"] == "idempotency_key_reused"
        replay = await game.client.patch(path, json={"name": "　しずく  "}, headers=headers)
        assert replay.json() == first.json()
        assert (await game.get(path)).json()["name"] == "あ" * 12
        assert (await game.get("/v1/adults")).json()[0]["name"] == "あ" * 12


@pytest.mark.parametrize(
    "name",
    [
        "",
        "　 ",
        "あ" * 13,
        "し\nずく",
        "\tみつ",
        "みつ\x00",
        "み\x7fつ",
        "み\x85つ",
        "み\u200bつ",
        123,
        None,
    ],
)
async def test_invalid_names_do_not_change_adult(sessions: Any, name: Any) -> None:
    async with GameClient(sessions, adults.router) as game:
        adult_id = await make_adult(sessions, game)
        path = f"/v1/adults/{adult_id}"
        response = await game.client.patch(
            path,
            json={"name": name},
            headers=game.headers | {"Idempotency-Key": str(uuid4())},
        )
        assert response.status_code == 422
        assert response.json()["error"]["code"] == "validation_error"
        assert (await game.get(path)).json()["name"] == "test"


async def test_rename_requires_auth_key_name_and_ownership(sessions: Any) -> None:
    async with GameClient(sessions, adults.router) as game:
        adult_id = await make_adult(sessions, game)
        path = f"/v1/adults/{adult_id}"
        key = {"Idempotency-Key": str(uuid4())}
        assert (
            await game.client.patch(path, json={"name": "みつ"}, headers=key)
        ).status_code == 401
        missing_key = await game.client.patch(path, json={"name": "みつ"}, headers=game.headers)
        assert missing_key.json()["error"]["code"] == "idempotency_key_required"
        missing_name = await game.client.patch(path, json={}, headers=game.headers | key)
        assert missing_name.json()["error"]["code"] == "validation_error"
        async with GameClient(sessions, adults.router) as other:
            for target in (path, "/v1/adults/missing"):
                response = await other.client.patch(
                    target,
                    json={"name": "みつ"},
                    headers=other.headers | {"Idempotency-Key": str(uuid4())},
                )
                assert response.status_code == 404
        assert (await game.get(path)).json()["name"] == "test"
