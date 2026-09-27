from __future__ import annotations

from contextlib import AsyncExitStack
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tsuyulabo_api.db.models import (
    ContestEntry,
    Decoration,
    Friendship,
    LedgerAccount,
    LedgerEntry,
    Week,
)
from tsuyulabo_api.routers import contest
from tsuyulabo_api.services.ledger import get_account, transfer

from .adult_fixtures import make_adult
from .game_support import GameClient


async def test_decorations_and_entry_reject_paid_items(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    async with GameClient(sessions, contest.decorations_router, contest.router) as game:
        adult_id = await make_adult(sessions, game)
        catalog = (await game.get("/v1/decorations")).json()
        assert {item["id"] for item in catalog["owned"]} == {"plain_vial", "leaf_background"}
        async with sessions() as session, session.begin():
            week = await session.scalar(select(Week).where(Week.user_id == game.user["id"]))
            week.rank = "silver"
            source = await get_account(session, "system:rewards", "research_points")
            wallet = await get_account(session, f"user:{game.user['id']}", "research_points")
            await transfer(session, source, wallet, 100, "presentation")
        earned = (await game.get("/v1/decorations")).json()
        assert {"rain_vial", "drop_ribbon", "banana_ornament"} <= {
            item["id"] for item in earned["owned"]
        }
        layout = catalog["layout"] | {"vial": "plain_vial"}
        key = str(uuid4())
        saved = await game.client.put(
            "/v1/decorations/layout",
            json=layout,
            headers=game.headers | {"Idempotency-Key": key},
        )
        assert saved.status_code == 200, saved.text
        replay = await game.client.put(
            "/v1/decorations/layout",
            json=layout,
            headers=game.headers | {"Idempotency-Key": key},
        )
        assert replay.json() == saved.json()
        first = await game.post("/v1/contest/current/entry", {"adult_id": adult_id})
        assert first.status_code == 200, first.text
        assert first.json()["layout"]["vial"] == "plain_vial"
        assert (
            await game.post("/v1/contest/current/entry", {"adult_id": adult_id})
        ).status_code == 409

    async with GameClient(sessions, contest.decorations_router, contest.router) as other:
        other_adult = await make_adult(sessions, other)
        async with sessions() as session, session.begin():
            session.add(Decoration(user_id=other.user["id"], item_id="rain_vial", source="paid"))
        layout = (await other.get("/v1/decorations")).json()["layout"] | {"vial": "rain_vial"}
        equipped = await other.client.put(
            "/v1/decorations/layout",
            json=layout,
            headers=other.headers | {"Idempotency-Key": str(uuid4())},
        )
        assert equipped.status_code == 200
        assert (
            await other.post("/v1/contest/current/entry", {"adult_id": other_adult})
        ).status_code == 422
        async with sessions() as session:
            assert not await session.scalar(
                select(ContestEntry).where(ContestEntry.user_id == other.user["id"])
            )


async def test_friends_vote_only_during_window_and_results(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    async with (
        GameClient(sessions, contest.router) as voter,
        GameClient(sessions, contest.router) as friend,
        GameClient(sessions, contest.router) as stranger,
    ):
        adult_id = await make_adult(sessions, friend)
        entry = (await friend.post("/v1/contest/current/entry", {"adult_id": adult_id})).json()
        assert (
            await voter.post("/v1/contest/current/votes", {"entry_id": entry["id"]})
        ).status_code == 409
        async with sessions() as session, session.begin():
            session.add(Friendship(user_id=voter.user["id"], friend_id=friend.user["id"]))
        voter.clock.advance(5 * 86400)
        stranger.clock.advance(5 * 86400)
        assert (
            await stranger.post("/v1/contest/current/votes", {"entry_id": entry["id"]})
        ).status_code == 404
        vote_key = str(uuid4())
        first_vote = await voter.post(
            "/v1/contest/current/votes", {"entry_id": entry["id"]}, vote_key
        )
        assert first_vote.json()["votes_left"] == 2
        assert (
            await voter.post("/v1/contest/current/votes", {"entry_id": entry["id"]}, vote_key)
        ).json() == first_vote.json()
        assert (
            await voter.post("/v1/contest/current/votes", {"entry_id": entry["id"]})
        ).status_code == 409
        voter.clock.advance(2 * 86400)
        result = (await voter.get("/v1/contest/results")).json()
        assert result["entries"][0]["votes"] == 1
        assert result["entries"][0]["rank"] == 1
        assert (await voter.get("/v1/contest/results")).json() == result
        async with sessions() as session:
            awards = list(
                await session.scalars(
                    select(LedgerEntry)
                    .join(LedgerAccount, LedgerAccount.id == LedgerEntry.account_id)
                    .where(
                        LedgerAccount.owner == f"user:{friend.user['id']}",
                        LedgerEntry.reason.in_(("contest_participation", "contest_placement")),
                    )
                )
            )
            assert sorted(row.amount for row in awards) == [5, 30]


async def test_three_votes_maximum_and_no_self_vote(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    async with AsyncExitStack() as stack:
        players = [
            await stack.enter_async_context(GameClient(sessions, contest.router)) for _ in range(5)
        ]
        voter, friends = players[0], players[1:]
        entries = []
        for player in players:
            adult_id = await make_adult(sessions, player)
            response = await player.post("/v1/contest/current/entry", {"adult_id": adult_id})
            assert response.status_code == 200, response.text
            entries.append(response.json()["id"])
        async with sessions() as session, session.begin():
            session.add_all(
                [
                    Friendship(user_id=voter.user["id"], friend_id=player.user["id"])
                    for player in friends
                ]
            )
        voter.clock.advance(5 * 86400)
        assert (
            await voter.post("/v1/contest/current/votes", {"entry_id": entries[0]})
        ).status_code == 404
        for remaining, entry_id in zip((2, 1, 0), entries[1:4], strict=True):
            assert (await voter.post("/v1/contest/current/votes", {"entry_id": entry_id})).json()[
                "votes_left"
            ] == remaining
        assert (
            await voter.post("/v1/contest/current/votes", {"entry_id": entries[4]})
        ).status_code == 409
