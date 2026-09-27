from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import delete, func, select
from tsuyulabo_api.db.models import (
    Adult,
    Friendship,
    Gift,
    Like,
    Notification,
    TeamSlot,
    User,
    Week,
)
from tsuyulabo_api.domain import constants as c
from tsuyulabo_api.domain.clock import game_day
from tsuyulabo_api.domain.friends import validate_code
from tsuyulabo_api.errors import APIError
from tsuyulabo_api.routers.users import CurrentUser as AuthenticatedUser
from tsuyulabo_api.services import week as week_service
from tsuyulabo_api.services.clock import game_now
from tsuyulabo_api.services.game import CurrentClock, CurrentUser, Session, reward
from tsuyulabo_api.services.idempotency import IdempotentRoute
from tsuyulabo_api.services.ledger import add_material, remove_material

router = APIRouter(prefix="/v1", route_class=IdempotentRoute)


class AddFriend(BaseModel):
    model_config = ConfigDict(extra="forbid")
    friend_code: str


class SendGift(BaseModel):
    model_config = ConfigDict(extra="forbid")
    material: str
    amount: int = Field(ge=1, le=c.FRIEND_GIFT_MAX, strict=True)


async def lock_pair(
    session: Session, user_id: str, friend_id: str, *, require_friend: bool = True
) -> User:
    # Symmetric actions take both locks in the same order, including reciprocal gifts.
    people = list(
        await session.scalars(
            select(User)
            .where(User.id.in_([user_id, friend_id]))
            .order_by(User.id)
            .with_for_update()
            .execution_options(populate_existing=True)
        )
    )
    if len(people) != 2:
        raise APIError("not_found", "フレンドが見つかりません", 404)
    if require_friend and await session.get(Friendship, (user_id, friend_id)) is None:
        raise APIError("not_found", "フレンドが見つかりません", 404)
    return next(person for person in people if person.id == friend_id)


@router.get("/friends")
async def list_friends(user: CurrentUser, session: Session) -> list[dict[str, Any]]:
    friends = await session.scalars(
        select(User)
        .join(Friendship, Friendship.friend_id == User.id)
        .where(Friendship.user_id == user.id)
        .order_by(User.display_name)
    )
    return [
        {
            "id": friend.id,
            "display_name": friend.display_name,
            "friend_code": friend.friend_code,
            "title": friend.title,
        }
        for friend in friends
    ]


@router.post("/friends", status_code=201)
async def add_friend(
    body: AddFriend, user: AuthenticatedUser, session: Session, clock: CurrentClock
) -> dict[str, Any]:
    if not validate_code(body.friend_code):
        raise APIError("validation_error", "フレンドコードが不正です", 422)
    friend = await session.scalar(select(User).where(User.friend_code == body.friend_code))
    if friend is None:
        raise APIError("not_found", "フレンドが見つかりません", 404)
    if friend.id == user.id:
        raise APIError("validation_error", "自分は登録できません", 422)
    await lock_pair(session, user.id, friend.id, require_friend=False)
    if await session.get(Friendship, (user.id, friend.id)):
        raise APIError("already_friends", "登録済みです", 409)
    for owner, other in ((user.id, friend.id), (friend.id, user.id)):
        count = await session.scalar(
            select(func.count()).select_from(Friendship).where(Friendship.user_id == owner)
        )
        if count >= c.FRIEND_CAPACITY:
            raise APIError("friend_limit", "フレンドは50人までです", 409)
        session.add(Friendship(user_id=owner, friend_id=other, created_at=game_now(clock, user)))
    return {"id": friend.id, "display_name": friend.display_name}


@router.delete("/friends/{friend_id}")
async def remove_friend(
    friend_id: str, user: AuthenticatedUser, session: Session
) -> dict[str, bool]:
    await lock_pair(session, user.id, friend_id)
    await session.execute(
        delete(Friendship).where(
            ((Friendship.user_id == user.id) & (Friendship.friend_id == friend_id))
            | ((Friendship.user_id == friend_id) & (Friendship.friend_id == user.id))
        )
    )
    return {"removed": True}


@router.get("/friends/{friend_id}/lab")
async def lab(
    friend_id: str, user: AuthenticatedUser, session: Session, clock: CurrentClock
) -> dict[str, Any]:
    friend = await lock_pair(session, user.id, friend_id)
    now = game_now(clock, friend)
    members = await session.execute(
        select(TeamSlot.slot, Adult)
        .join(Adult, TeamSlot.adult_id == Adult.id)
        .where(TeamSlot.user_id == friend.id, Adult.user_id == friend.id)
        .order_by(TeamSlot.slot)
    )
    week = await session.scalar(
        select(Week).where(Week.user_id == friend.id, Week.status == "active")
    )
    current = None
    if week:
        detail = await week_service.payload(session, week, now)
        current = {
            "stage": detail["stage"],
            "research_day": detail["research_day"],
            "fly": {key: detail["fly"][key] for key in ("hunger", "cleanliness", "mood_label")},
        }
    flies = await session.scalars(select(Adult).where(Adult.user_id == friend.id))
    return {
        "user": {"id": friend.id, "display_name": friend.display_name},
        "adults": [public_adult(adult) for adult in flies],
        "team": {"members": [public_adult(adult) | {"slot": slot} for slot, adult in members]},
        "week": current,
    }


def public_adult(adult: Adult) -> dict[str, Any]:
    # Allowlist the fields rendered by friend cards; owner serializers grow independently.
    return {
        "id": adult.id,
        "name": adult.name,
        "sex": adult.sex,
        "strain": adult.strain,
        "stars": adult.stars,
        "level": adult.level,
    }


@router.post("/friends/{friend_id}/like")
async def like(
    friend_id: str, user: AuthenticatedUser, session: Session, clock: CurrentClock
) -> dict[str, bool]:
    await lock_pair(session, user.id, friend_id)
    now = game_now(clock, user)
    day = game_day(now)
    if await session.get(Like, (user.id, friend_id, day)):
        raise APIError("daily_limit_reached", "今日はいいね済みです", 409)
    session.add(Like(from_user_id=user.id, to_user_id=friend_id, day=day))
    session.add(
        Notification(
            user_id=friend_id,
            kind="like",
            created_at=now,
            payload={"user_id": user.id, "display_name": user.display_name},
        )
    )
    return {"liked": True}


@router.post("/friends/{friend_id}/gift")
async def gift(
    friend_id: str, body: SendGift, user: AuthenticatedUser, session: Session, clock: CurrentClock
) -> dict[str, Any]:
    await lock_pair(session, user.id, friend_id)
    now, day = game_now(clock, user), game_day(game_now(clock, user))
    if body.material not in c.MATERIALS:
        raise APIError("validation_error", "材料が不正です", 422)
    if await session.get(Gift, (user.id, day)):
        raise APIError("daily_limit_reached", "今日はおすそわけ済みです", 409)
    await remove_material(session, user.id, body.material, body.amount)
    await add_material(session, friend_id, body.material, body.amount)
    session.add(
        Gift(
            from_user_id=user.id,
            to_user_id=friend_id,
            day=day,
            material=body.material,
            amount=body.amount,
        )
    )
    await reward(
        session, user.id, "research_points", c.FRIEND_GIFT_RP, "friend_gift", day.isoformat()
    )
    payload = {
        "user_id": user.id,
        "display_name": user.display_name,
        "material": body.material,
        "amount": body.amount,
    }
    session.add(Notification(user_id=friend_id, kind="gift", created_at=now, payload=payload))
    return payload | {"research_points": c.FRIEND_GIFT_RP}


@router.get("/notifications")
async def notifications(user: CurrentUser, session: Session) -> list[dict[str, Any]]:
    return [
        {
            "id": n.id,
            "kind": n.kind,
            "payload": n.payload,
            "created_at": n.created_at,
            "read_at": n.read_at,
        }
        for n in await session.scalars(
            select(Notification)
            .where(Notification.user_id == user.id)
            .order_by(Notification.created_at.desc())
        )
    ]
