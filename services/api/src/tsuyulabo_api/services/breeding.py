from __future__ import annotations

from datetime import datetime, timedelta
from random import Random

from sqlalchemy.ext.asyncio import AsyncSession
from tsuyulabo_api.domain import genetics
from tsuyulabo_api.domain.clock import day_start, game_day
from tsuyulabo_api.errors import APIError
from tsuyulabo_api.services.adults import owned


async def draw_egg(
    session: AsyncSession,
    user_id: str,
    parents: tuple[str, str] | None,
    now: datetime,
    rng: Random,
) -> genetics.Offspring:
    if parents is None:
        return genetics.Offspring(genetics.normal_egg(rng), 0)
    mother = await owned(session, user_id, parents[0])
    father = await owned(session, user_id, parents[1])
    if mother.id == father.id or mother.sex != "f" or father.sex != "m":
        raise APIError("validation_error", "母親（♀）と父親（♂）を順番に選んでください", 422)
    day = game_day(now)
    boundary = day_start(day - timedelta(days=day.weekday()))
    for parent in (mother, father):
        if parent.last_parent_week is not None and parent.last_parent_week >= boundary:
            raise APIError("parent_already_used", "この親は今週すでに交配しています", 409)
    child = genetics.breed(rng, mother.genotype, father.genotype)
    mother.last_parent_week = father.last_parent_week = boundary
    return child
