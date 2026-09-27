from __future__ import annotations

import asyncio
from random import Random
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import select
from tsuyulabo_api.db.models import Adult, MatingProposal, Notification, PendingEgg, Week
from tsuyulabo_api.domain import genetics
from tsuyulabo_api.routers import friends, home, mating, weeks

from .adult_fixtures import make_adult
from .game_support import GameClient

PATH = "/v1/weeks/friend-mating"


async def pair(sessions: Any, a: GameClient, b: GameClient) -> dict[str, str]:
    assert (await a.post("/v1/friends", {"friend_code": b.user["friend_code"]})).status_code == 201
    mother = await make_adult(
        sessions,
        a,
        genotype=genetics.wild_type("f")
        | {
            "w": ["w", "w"],
            "Cy": ["Cy", "+"],
        },
    )
    father = await make_adult(
        sessions,
        b,
        sex="m",
        genotype=genetics.wild_type("m")
        | {
            "Cy": ["Cy", "+"],
        },
    )
    return {"friend_id": b.user["id"], "adult_id": mother, "friend_adult_id": father}


async def test_accept_draws_two_fixed_hidden_eggs_and_starts_once(
    sessions: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(mating, "rng", lambda: Random(42))
    async with (
        GameClient(sessions, weeks.router, friends.router, home.router) as a,
        GameClient(sessions, weeks.router, friends.router) as b,
    ):
        body = await pair(sessions, a, b)
        assert (await a.post("/v1/weeks")).status_code == 201
        key = str(uuid4())
        proposed = await a.post(PATH, body, key=key)
        assert proposed.status_code == 201, proposed.text
        assert (await a.post(PATH, body, key=key)).json() == proposed.json()
        proposal_id = proposed.json()["id"]
        incoming = (await b.get(PATH)).json()["incoming"]
        assert incoming[0]["id"] == proposal_id
        assert (await a.get(PATH)).json()["outgoing"][0]["status"] == "pending"
        key = str(uuid4())
        accepted = await b.post(f"{PATH}/{proposal_id}/accept", key=key)
        assert accepted.status_code == 200, accepted.text
        assert (await b.post(f"{PATH}/{proposal_id}/accept", key=key)).json() == accepted.json()
        assert (await b.post(f"{PATH}/{proposal_id}/accept")).status_code == 409
        async with sessions() as session:
            mother = await session.get(Adult, body["adult_id"])
            father = await session.get(Adult, body["friend_adult_id"])
            random = Random(42)
            expected = [genetics.breed(random, mother.genotype, father.genotype) for _ in range(2)]
            assert expected[0] != expected[1]
            assert mother.last_parent_week == father.last_parent_week
            eggs = {egg.user_id: egg for egg in await session.scalars(select(PendingEgg))}
            for owner, child in zip((a.user["id"], b.user["id"]), expected, strict=True):
                assert eggs[owner].genotype == child.genotype
                assert eggs[owner].lethal_redraws == child.lethal_redraws
            notes = list(await session.scalars(select(Notification)))
            assert sorted(n.kind for n in notes) == [
                "mating_accepted",
                "mating_accepted",
                "mating_pending",
                "mating_pending",
            ]
        public_eggs = (await a.get("/v1/weeks/pending-eggs")).json()
        assert len(public_eggs) == 1
        assert not any(word in str(public_eggs) for word in ("genotype", "sex", "redraws"))
        own_egg = public_eggs[0]["id"]
        assert (await b.post("/v1/weeks", {"pending_egg_id": own_egg})).status_code == 404
        assert (await a.post("/v1/weeks", {"pending_egg_id": own_egg})).status_code == 409
        await a.advance(to="eclosion")
        assert (await a.post("/v1/weeks/current/eclose")).status_code == 200
        key = str(uuid4())
        started = await a.post("/v1/weeks", {"pending_egg_id": own_egg}, key=key)
        assert started.status_code == 201, started.text
        assert (
            await a.post("/v1/weeks", {"pending_egg_id": own_egg}, key=key)
        ).json() == started.json()
        assert "genotype" not in started.text
        assert "genotype" not in (await a.get("/v1/home")).text
        assert (await a.get("/v1/weeks/pending-eggs")).json() == []
        async with sessions() as session:
            week = await session.get(Week, started.json()["id"])
            assert week.egg_genotype == expected[0].genotype
            assert week.lethal_redraws == expected[0].lethal_redraws
            assert (week.mother_id, week.father_id) == (body["adult_id"], body["friend_adult_id"])
        await a.advance(to="eclosion")
        await a.post("/v1/weeks/current/eclose")
        assert (await a.post("/v1/weeks", {"pending_egg_id": own_egg})).json()["error"][
            "code"
        ] == "egg_already_used"


@pytest.mark.parametrize("who", ["proposer", "recipient"])
async def test_expiry_at_48_hours_with_either_dev_clock(sessions: Any, who: str) -> None:
    async with (
        GameClient(sessions, weeks.router, friends.router) as a,
        GameClient(sessions, weeks.router) as b,
    ):
        body = await pair(sessions, a, b)
        proposal = (await a.post(PATH, body)).json()
        advancing = a if who == "proposer" else b
        await advancing.advance(hours=47)
        assert (await b.get(PATH)).json()["incoming"][0]["status"] == "pending"
        await advancing.advance(hours=1)
        assert (await b.get(PATH)).json()["incoming"][0]["status"] == "expired"
        for action in ("accept", "decline"):
            assert (await b.post(f"{PATH}/{proposal['id']}/{action}")).status_code == 409
        assert (await advancing.post("/v1/dev/time/reset")).status_code == 409
        assert (await a.post(PATH, body)).status_code == 409
        async with sessions() as session:
            assert list(await session.scalars(select(PendingEgg))) == []
            assert (await session.get(Adult, body["adult_id"])).last_parent_week is None


async def test_permissions_decline_pair_limit_and_next_week(sessions: Any) -> None:
    async with (
        GameClient(sessions, weeks.router, friends.router) as a,
        GameClient(sessions, weeks.router, friends.router) as b,
        GameClient(sessions, weeks.router) as stranger,
    ):
        body = await pair(sessions, a, b)
        assert (await stranger.post(PATH, body)).status_code == 404
        assert (await stranger.get(f"{PATH}/options/{b.user['id']}")).status_code == 404
        options = (await a.get(f"{PATH}/options/{b.user['id']}")).json()
        assert options[0]["genotype"]["sex"] == "m"
        assert options[0]["available"] is True
        same = await make_adult(sessions, b)
        assert (await a.post(PATH, body | {"friend_adult_id": same})).status_code == 422
        for invalid in (
            {"adult_id": body["friend_adult_id"]},
            {"friend_adult_id": body["adult_id"]},
            {"friend_id": a.user["id"]},
        ):
            assert (await a.post(PATH, body | invalid)).status_code == 404
        assert (await a.post(PATH, body | {"seed": 42})).status_code == 422
        proposal = (await a.post(PATH, body)).json()
        reverse = {
            "friend_id": a.user["id"],
            "adult_id": body["friend_adult_id"],
            "friend_adult_id": body["adult_id"],
        }
        assert (await b.post(PATH, reverse)).status_code == 409
        assert (await stranger.get(PATH)).json() == {"incoming": [], "outgoing": []}
        for client in (a, stranger):
            for action in ("accept", "decline"):
                assert (await client.post(f"{PATH}/{proposal['id']}/{action}")).status_code == 404
        key = str(uuid4())
        declined = await b.post(f"{PATH}/{proposal['id']}/decline", key=key)
        assert declined.json()["status"] == "declined"
        assert (await b.post(f"{PATH}/{proposal['id']}/decline", key=key)).json() == declined.json()
        assert (await a.post(PATH, body)).status_code == 409
        async with sessions() as session:
            assert (await session.get(Adult, body["adult_id"])).last_parent_week is None
            assert (
                len(
                    list(
                        await session.scalars(
                            select(Notification).where(Notification.kind == "mating_declined")
                        )
                    )
                )
                == 2
            )
        await a.advance(hours=168)
        assert (await a.post(PATH, body)).status_code == 201


async def test_unfriending_rechecks_accept_but_keeps_accepted_eggs(sessions: Any) -> None:
    async with (
        GameClient(sessions, weeks.router, friends.router) as a,
        GameClient(sessions, weeks.router) as b,
    ):
        body = await pair(sessions, a, b)
        proposal = (await a.post(PATH, body)).json()
        response = await a.client.delete(
            f"/v1/friends/{b.user['id']}", headers=a.headers | {"Idempotency-Key": str(uuid4())}
        )
        assert response.status_code == 200
        assert (await b.post(f"{PATH}/{proposal['id']}/accept")).status_code == 404
        await a.post("/v1/friends", {"friend_code": b.user["friend_code"]})
        assert (await b.post(f"{PATH}/{proposal['id']}/accept")).status_code == 200
        await a.client.delete(
            f"/v1/friends/{b.user['id']}", headers=a.headers | {"Idempotency-Key": str(uuid4())}
        )
        egg = (await b.get("/v1/weeks/pending-eggs")).json()[0]
        assert (await b.post("/v1/weeks", {"pending_egg_id": egg["id"]})).status_code == 201


async def test_competing_accepts_and_normal_breeding_share_parent_limit(sessions: Any) -> None:
    async with (
        GameClient(sessions, weeks.router, friends.router) as a,
        GameClient(sessions, weeks.router) as b,
    ):
        body = await pair(sessions, a, b)
        proposal = (await a.post(PATH, body)).json()
        another = await make_adult(sessions, b, sex="m")
        competing = (await a.post(PATH, body | {"friend_adult_id": another})).json()
        responses = await asyncio.gather(
            *(b.post(f"{PATH}/{item['id']}/accept") for item in (proposal, competing))
        )
        assert sorted(r.status_code for r in responses) == [200, 409]
        own_father = await make_adult(sessions, a, sex="m")
        assert (
            await a.post("/v1/weeks", {"parents": [body["adult_id"], own_father]})
        ).status_code == 409
        assert (await a.post(PATH, body | {"friend_adult_id": another})).status_code == 409
        async with sessions() as session:
            assert len(list(await session.scalars(select(PendingEgg)))) == 2
            assert (
                len(
                    list(
                        await session.scalars(
                            select(MatingProposal).where(MatingProposal.status == "accepted")
                        )
                    )
                )
                == 1
            )


async def test_normal_breeding_after_proposal_prevents_accept(sessions: Any) -> None:
    async with (
        GameClient(sessions, weeks.router, friends.router) as a,
        GameClient(sessions, weeks.router) as b,
    ):
        body = await pair(sessions, a, b)
        proposal = (await a.post(PATH, body)).json()
        father = await make_adult(sessions, a, sex="m")
        await a.post("/v1/weeks", {"parents": [body["adult_id"], father]})
        assert (await b.post(f"{PATH}/{proposal['id']}/accept")).json()["error"][
            "code"
        ] == "parent_already_used"
        assert (await b.get("/v1/weeks/pending-eggs")).json() == []


async def test_pending_source_validation(sessions: Any) -> None:
    async with GameClient(sessions, weeks.router) as a:
        assert (await a.post("/v1/weeks", {"pending_egg_id": "missing"})).status_code == 404
        assert (
            await a.post("/v1/weeks", {"pending_egg_id": "id", "parents": ["a", "b"]})
        ).status_code == 422
