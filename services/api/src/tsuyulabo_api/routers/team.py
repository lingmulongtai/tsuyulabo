from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict
from tsuyulabo_api.db.models import TeamSlot
from tsuyulabo_api.domain.constants import TEAM_CAPACITY
from tsuyulabo_api.errors import APIError
from tsuyulabo_api.services import adults, team
from tsuyulabo_api.services.clock import game_now
from tsuyulabo_api.services.game import Brain, CurrentClock, CurrentUser, Session
from tsuyulabo_api.services.idempotency import IdempotentRoute

router = APIRouter(prefix="/v1/team", route_class=IdempotentRoute)


class TeamRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    adult_ids: list[str]


@router.put("")
async def set_team(
    body: TeamRequest, user: CurrentUser, session: Session, clock: CurrentClock, brain: Brain
) -> dict[str, Any]:
    if len(body.adult_ids) > TEAM_CAPACITY:
        raise APIError("team_full", "チームは5匹までです", 409)
    if len(set(body.adult_ids)) != len(body.adult_ids):
        raise APIError("validation_error", "同じ成虫は選べません", 422)
    selected = [await adults.owned(session, user.id, adult_id) for adult_id in body.adult_ids]
    now = game_now(clock, user)
    members = await team.settle(session, user.id, now, brain)
    # Park each bag on its owner when removed. Reordering never discards contents,
    # fractional accrual, or RNG state, and off-team time earns nothing.
    for slot, adult in members:
        adult.gathering = slot.bag
        await session.delete(slot)
    await session.flush()
    for index, adult in enumerate(selected):
        session.add(
            TeamSlot(
                user_id=user.id,
                slot=index,
                adult_id=adult.id,
                bag=adult.gathering,
                last_computed_at=now,
            )
        )
        adult.gathering = {}
    await session.flush()
    return team.payload(await team.settle(session, user.id, now, brain))


@router.get("")
async def get_team(
    user: CurrentUser, session: Session, clock: CurrentClock, brain: Brain
) -> dict[str, Any]:
    return team.payload(await team.settle(session, user.id, game_now(clock, user), brain))


@router.post("/collect")
async def collect(
    user: CurrentUser, session: Session, clock: CurrentClock, brain: Brain
) -> dict[str, Any]:
    members = await team.settle(session, user.id, game_now(clock, user), brain)
    result = await team.collect(session, user.id, members)
    return result | {"team": team.payload(members)}
