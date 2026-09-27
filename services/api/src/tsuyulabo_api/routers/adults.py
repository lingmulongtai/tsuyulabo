from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from sqlalchemy import select
from tsuyulabo_api.db.models import Adult
from tsuyulabo_api.domain import adults as rules
from tsuyulabo_api.errors import APIError
from tsuyulabo_api.services import adults, team
from tsuyulabo_api.services.clock import game_now
from tsuyulabo_api.services.game import Brain, CurrentClock, CurrentUser, Session, rng
from tsuyulabo_api.services.idempotency import IdempotentRoute
from tsuyulabo_api.services.ledger import get_account, transfer

router = APIRouter(prefix="/v1/adults", route_class=IdempotentRoute)


@router.get("")
async def list_adults(
    user: CurrentUser, session: Session, clock: CurrentClock, brain: Brain
) -> list[dict[str, Any]]:
    await team.settle(session, user.id, game_now(clock, user), brain)
    return [
        adults.payload(adult, brain)
        for adult in await session.scalars(
            select(Adult).where(Adult.user_id == user.id).order_by(Adult.created_at.desc())
        )
    ]


@router.get("/{adult_id}")
async def detail(
    adult_id: str, user: CurrentUser, session: Session, clock: CurrentClock, brain: Brain
) -> dict[str, Any]:
    adult = await adults.owned(session, user.id, adult_id)
    await team.settle(session, user.id, game_now(clock, user), brain)
    return adults.payload(adult, brain)


@router.post("/{adult_id}/level-up")
async def level_up(
    adult_id: str, user: CurrentUser, session: Session, clock: CurrentClock, brain: Brain
) -> dict[str, Any]:
    adult = await adults.owned(session, user.id, adult_id)
    if adult.level >= rules.level_cap(adult.stars):
        raise APIError("level_cap_reached", "レベルの上限です", 409)
    await team.settle(session, user.id, game_now(clock, user), brain)
    wallet = await get_account(session, f"user:{user.id}", "shizuku")
    sink = await get_account(session, "system:level_up", "shizuku")
    cost = rules.level_up_cost(adult.level)
    await transfer(session, wallet, sink, cost, "level_up", adult.id)
    state, _ = rules.level_up(adults.progress(adult), cost, rng())
    adults.apply_progress(adult, state)
    return adults.payload(adult, brain) | {"cost": cost}
