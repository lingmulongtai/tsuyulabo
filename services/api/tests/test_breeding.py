from __future__ import annotations

import asyncio
from copy import deepcopy
from datetime import timedelta
from random import Random
from typing import Any
from uuid import uuid4

import pytest
from sqlalchemy import select
from tsuyulabo_api.db.models import Adult, Week
from tsuyulabo_api.domain import genetics
from tsuyulabo_api.routers import home, weeks

from .adult_fixtures import make_adult
from .game_support import GameClient


async def test_inherited_egg_is_hidden_fixed_and_revealed(sessions: Any) -> None:
    async with GameClient(sessions, weeks.router, home.router) as game:
        mother_genes = genetics.wild_type("f") | {"w": ["w", "w"]}
        mother = await make_adult(sessions, game, genotype=mother_genes, strain="white")
        father = await make_adult(sessions, game, sex="m")
        key = str(uuid4())
        response = await game.post("/v1/weeks", {"parents": [mother, father]}, key=key)
        assert response.status_code == 201, response.text
        assert (
            await game.post("/v1/weeks", {"parents": [mother, father]}, key=key)
        ).json() == response.json()
        for payload in (
            response.json(),
            (await game.get("/v1/weeks/current")).json(),
            (await game.get("/v1/home")).json()["week"],
        ):
            assert "genotype" not in str(payload) and "lethal_redraws" not in payload
        async with sessions() as session:
            week = await session.get(Week, response.json()["id"])
            egg = deepcopy(week.egg_genotype)
            assert week.mother_id == mother and week.father_id == father
            assert egg["w"] == (["w"] if egg["sex"] == "m" else ["w", "+"])
        await game.advance(to="eclosion")
        result = (await game.post("/v1/weeks/current/eclose")).json()
        adult = result["adult"]
        assert adult["sex"] == egg["sex"]
        assert adult["phenotypes"] == genetics.phenotypes(adult["genotype"])
        if result["tier"] != 3:
            assert adult["genotype"] == egg
        assert (await game.post("/v1/weeks", {"parents": [mother, father]})).status_code == 409
        game.clock.advance(7 * 86400)
        assert (await game.post("/v1/weeks", {"parents": [mother, father]})).status_code == 201


@pytest.mark.parametrize(
    "body", [{"parents": []}, {"parents": ["a"]}, {"parents": ["a", "b", "c"]}, {"genotype": {}}]
)
async def test_invalid_request_shape(sessions: Any, body: dict) -> None:
    async with GameClient(sessions, weeks.router) as game:
        assert (await game.post("/v1/weeks", body)).status_code == 422


async def test_parent_ownership_sex_reuse_and_clock_reset(sessions: Any) -> None:
    async with GameClient(sessions, weeks.router) as game, GameClient(sessions) as other:
        mother = await make_adult(sessions, game)
        father = await make_adult(sessions, game, sex="m")
        foreign = await make_adult(sessions, other, sex="m")
        for parents, status in (
            ([mother, foreign], 404),
            ([mother, "missing"], 404),
            ([father, mother], 422),
            ([mother, mother], 422),
        ):
            assert (await game.post("/v1/weeks", {"parents": parents})).status_code == status
        async with sessions() as session, session.begin():
            adult = await session.get(Adult, mother)
            adult.last_parent_week = game.clock.now() + timedelta(days=7)
        assert (await game.post("/v1/weeks", {"parents": [mother, father]})).json()["error"][
            "code"
        ] == "parent_already_used"
        assert (await game.post("/v1/weeks")).status_code == 201


async def test_concurrent_breeding(sessions: Any) -> None:
    async with GameClient(sessions, weeks.router) as game:
        mother = await make_adult(sessions, game)
        father = await make_adult(sessions, game, sex="m")
        responses = await asyncio.gather(
            *(game.post("/v1/weeks", {"parents": [mother, father]}) for _ in range(2))
        )
        assert sorted(r.status_code for r in responses) == [201, 409]
        async with sessions() as session:
            assert (
                len(list(await session.scalars(select(Week).where(Week.status == "active")))) == 1
            )


async def test_lethal_redraws_persist_and_rainbow_mutates_one_allele(
    sessions: Any,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mother_genes = genetics.wild_type("f") | {"Cy": ["Cy", "+"]}
    father_genes = genetics.wild_type("m") | {"Cy": ["Cy", "+"]}
    seed = next(
        s
        for s in range(100)
        if genetics.breed(Random(s), mother_genes, father_genes).lethal_redraws
    )
    monkeypatch.setattr(weeks, "rng", lambda: Random(seed))
    monkeypatch.setattr(weeks.eclosion, "roll_tier", lambda *args: 3)
    async with GameClient(sessions, weeks.router) as game:
        mother = await make_adult(sessions, game, genotype=mother_genes, strain="curly")
        father = await make_adult(sessions, game, sex="m", genotype=father_genes, strain="curly")
        response = await game.post("/v1/weeks", {"parents": [mother, father]})
        async with sessions() as session:
            week = await session.get(Week, response.json()["id"])
            egg, rejected = deepcopy(week.egg_genotype), week.lethal_redraws
            assert rejected > 0
        await game.advance(to="eclosion")
        result = (await game.post("/v1/weeks/current/eclose")).json()
        assert result["lethal_redraws"] == rejected
        adult = result["adult"]
        assert adult["mutation"] is not None
        assert (
            sum(
                a != b
                for locus in genetics.LOCI
                for a, b in zip(egg[locus], adult["genotype"][locus], strict=True)
            )
            == 1
        )
        async with sessions() as session:
            assert (await session.get(Week, response.json()["id"])).egg_genotype == egg
