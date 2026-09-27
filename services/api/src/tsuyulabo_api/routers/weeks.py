from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from sqlalchemy import func, select
from tsuyulabo_api.db.models import Adult, Friendship, LarvaState, Notification, Week
from tsuyulabo_api.domain import constants as c
from tsuyulabo_api.domain import eclosion, lifecycle, names
from tsuyulabo_api.errors import APIError
from tsuyulabo_api.services import week as service
from tsuyulabo_api.services.brain_state import snapshot as brain_snapshot
from tsuyulabo_api.services.brain_state import store as store_brain
from tsuyulabo_api.services.clock import game_now
from tsuyulabo_api.services.game import Brain, CurrentClock, CurrentUser, Session, reward, rng
from tsuyulabo_api.services.idempotency import IdempotentRoute

router = APIRouter(prefix="/v1/weeks", route_class=IdempotentRoute)


@router.post("", status_code=201)
async def start_week(
    user: CurrentUser, session: Session, clock: CurrentClock, brain: Brain
) -> dict[str, Any]:
    if await session.scalar(
        select(Week.id).where(Week.user_id == user.id, Week.status == "active")
    ):
        raise APIError("week_already_active", "育成中の週があります", 409)
    now = game_now(clock, user)
    week = Week(user_id=user.id, started_at=now)
    session.add(week)
    await session.flush()
    larva = LarvaState(week_id=week.id, last_computed_at=now)
    store_brain(larva, brain.new(), brain)
    session.add(larva)
    await session.flush()
    return await service.payload(session, week, now)


@router.get("/current")
async def read_current(user: CurrentUser, session: Session, clock: CurrentClock) -> dict[str, Any]:
    return await service.payload(
        session, await service.current(session, user.id), game_now(clock, user)
    )


@router.get("/current/presentation")
async def read_presentation(
    user: CurrentUser, session: Session, clock: CurrentClock
) -> dict[str, Any]:
    week, now = await service.current(session, user.id), game_now(clock, user)
    if not lifecycle.ready_to_eclose(week.started_at, now):
        raise APIError("not_available_today", "発表会は7日目の夜からです", 409)
    return await service.presentation_payload(session, week, now)


@router.post("/current/eclose")
async def eclose(
    user: CurrentUser, session: Session, clock: CurrentClock, brain: Brain
) -> dict[str, Any]:
    week, now = await service.current(session, user.id), game_now(clock, user)
    if not lifecycle.ready_to_eclose(week.started_at, now):
        raise APIError("not_available_today", "羽化は7日目の夜からです", 409)
    count = await session.scalar(
        select(func.count()).select_from(Adult).where(Adult.user_id == user.id)
    )
    if count >= c.ADULT_CAPACITY:
        raise APIError("adult_capacity_reached", "飼育室がいっぱいです", 409)
    result = await service.presentation_payload(session, week, now)
    log = service.domain_events(await service.events(session, week))
    temperatures = [e.score for e in log if e.kind == "temperature"]
    random = rng()
    roll = eclosion.roll(
        random,
        result["rank"],
        sum(temperatures) / len(temperatures) if temperatures else 0,
        any(e.hit for e in log if e.kind == "pupation_site"),
    )
    larva = await session.get(LarvaState, week.id)
    snapshot, params = brain.eclose(
        brain_snapshot(larva), list(roll.traits), roll.sex, random.getrandbits(63)
    )
    taken = set(await session.scalars(select(Adult.name).where(Adult.user_id == user.id)))
    adult = Adult(
        user_id=user.id,
        week_id=week.id,
        name=names.pick_name(random, taken, strain=roll.strain),
        sex=roll.sex,
        strain=roll.strain,
        stars=roll.stars,
        traits=list(roll.traits),
        brain_params=params,
        skills=larva.skills,
        created_at=now,
    )
    store_brain(adult, snapshot, brain)
    session.add(adult)
    await session.flush()
    for currency in ("shizuku", "research_points"):
        await reward(session, user.id, currency, result[currency], "presentation", week.id)
    week.status, week.eclosed_at, week.adult_id = "eclosed", now, adult.id
    week.rank, week.points = result["rank"], result["points"]
    for friend_id in await session.scalars(
        select(Friendship.friend_id).where(Friendship.user_id == user.id)
    ):
        session.add(
            Notification(
                user_id=friend_id,
                kind="eclosion",
                created_at=now,
                payload={
                    "user_id": user.id,
                    "display_name": user.display_name,
                    "rank": week.rank,
                    "adult_id": adult.id,
                },
            )
        )
    return {
        "omen_sequence": roll.omen_sequence,
        "tier": roll.tier,
        "adult": {
            "id": adult.id,
            "name": adult.name,
            "sex": adult.sex,
            "strain": adult.strain,
            "stars": adult.stars,
            "traits": adult.traits,
            "level": adult.level,
            "skills": adult.skills,
            "preferences": adult.preferences,
        },
    }


@router.get("")
async def past_weeks(user: CurrentUser, session: Session) -> list[dict[str, Any]]:
    return [
        {
            "id": w.id,
            "rank": w.rank,
            "points": w.points,
            "adult_id": w.adult_id,
            "started_at": w.started_at,
            "eclosed_at": w.eclosed_at,
        }
        for w in await session.scalars(
            select(Week)
            .where(Week.user_id == user.id, Week.status == "eclosed")
            .order_by(Week.started_at.desc())
        )
    ]
