"""Inline, asynchronous-in-story territory bouts with private stored replays."""

from __future__ import annotations

import hashlib
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from tsuyulabo_api.brain_adapter import BrainAdapter
from tsuyulabo_api.db.models import Adult, Friendship, SumoBout, User
from tsuyulabo_api.domain.clock import game_day
from tsuyulabo_api.domain.sumo import run
from tsuyulabo_api.errors import APIError
from tsuyulabo_api.services.brain_state import snapshot
from tsuyulabo_api.services.clock import game_now
from tsuyulabo_api.services.game import CurrentClock, CurrentUser, Session, reward
from tsuyulabo_api.services.idempotency import IdempotentRoute

router = APIRouter(prefix="/v1/sumo", route_class=IdempotentRoute)


class StartBout(BaseModel):
    model_config = ConfigDict(extra="forbid")
    adult_id: str
    opponent_id: str


class Challenger(BaseModel):
    id: str
    name: str
    strain: str
    level: int
    traits: list[str]
    owner_name: str


class Challenges(BaseModel):
    males: list[Challenger]
    opponents: list[Challenger]
    remaining: int
    streak: int


class BoutSummary(BaseModel):
    id: str
    adult_id: str
    opponent_id: str | None
    opponent_name: str
    won: bool
    reward: int
    created_at: datetime


class SumoFrame(BaseModel):
    tick: int
    positions: list[float]
    actions: list[str]
    push: list[float]
    retreats: list[int]


class SumoResult(BaseModel):
    winner: int
    reason: str
    frames: list[SumoFrame]


class BoutReplay(BoutSummary):
    replay: SumoResult


def _seed(*parts: str) -> int:
    return int.from_bytes(hashlib.sha256(":|:".join(parts).encode()).digest()[:8], "big")


def _view(adult: Adult, owner: str, *, public: bool = False) -> Challenger:
    return Challenger(
        id=adult.id,
        name=adult.name,
        strain=adult.strain,
        level=adult.level,
        traits=[] if public else adult.traits,
        owner_name=owner,
    )


def _house(day: str) -> Challenger:
    week = datetime.fromisoformat(day).isocalendar()
    return Challenger(
        id="house",
        name="おうちのライバル",
        strain="wild",
        level=2,
        traits=["brave"] if week.week % 2 else ["wanderer"],
        owner_name="ツユラボ",
    )


def _week_key(day: str) -> str:
    year, week, _ = datetime.fromisoformat(day).isocalendar()
    return f"{year}-W{week:02d}"


async def _history(session: Session, user_id: str) -> list[SumoBout]:
    return list(
        await session.scalars(
            select(SumoBout)
            .where(SumoBout.user_id == user_id)
            .order_by(SumoBout.game_day.desc(), SumoBout.daily_index.desc())
        )
    )


@router.get("/challenges")
async def challenges(user: CurrentUser, session: Session, clock: CurrentClock) -> Challenges:
    day = game_day(game_now(clock, user)).isoformat()
    own = list(
        await session.scalars(select(Adult).where(Adult.user_id == user.id, Adult.sex == "m"))
    )
    rows = (
        await session.execute(
            select(Adult, User)
            .join(User, User.id == Adult.user_id)
            .join(Friendship, Friendship.friend_id == User.id)
            .where(Friendship.user_id == user.id, Adult.sex == "m")
        )
    ).all()
    history = await _history(session, user.id)
    streak = 0
    for bout in history:
        if not bout.won:
            break
        streak += 1
    return Challenges(
        males=[_view(adult, "あなた") for adult in own],
        opponents=[
            _house(day),
            *[_view(adult, person.display_name, public=True) for adult, person in rows],
        ],
        remaining=max(0, 3 - sum(bout.game_day == day for bout in history)),
        streak=streak,
    )


@router.post("/bouts")
async def start(
    body: StartBout, user: CurrentUser, session: Session, clock: CurrentClock
) -> BoutReplay:
    # The user row serializes the daily counter on PostgreSQL.
    await session.scalar(select(User).where(User.id == user.id).with_for_update())
    now = game_now(clock, user)
    day = game_day(now).isoformat()
    history = await _history(session, user.id)
    count = sum(bout.game_day == day for bout in history)
    if count >= 3:
        raise APIError("daily_limit_reached", "今日はもう3戦しました", 409)
    adult = await session.scalar(
        select(Adult).where(Adult.id == body.adult_id, Adult.user_id == user.id, Adult.sex == "m")
    )
    if adult is None:
        raise APIError("not_found", "オスの成虫が見つかりません", 404)
    if body.opponent_id == "house":
        rival = _house(day)
        brain = BrainAdapter()
        rival_state = brain.api.new_fly_state(
            brain.api.generate_individual(rival.traits, "m", _seed(_week_key(day), "house") % 2**31)
        )
        opponent_id = None
    else:
        other = await session.scalar(
            select(Adult)
            .join(Friendship, Friendship.friend_id == Adult.user_id)
            .where(Friendship.user_id == user.id, Adult.id == body.opponent_id, Adult.sex == "m")
        )
        if other is None:
            raise APIError("not_found", "対戦相手が見つかりません", 404)
        rival = _view(other, "フレンド", public=True)
        rival_state = BrainAdapter().restore(snapshot(other))
        opponent_id = other.id
    brain = BrainAdapter()
    own_state = brain.restore(snapshot(adult))
    result = run(
        lambda observation: brain.api.sumo_policy(own_state, observation),
        lambda observation: brain.api.sumo_policy(rival_state, observation),
        _seed(day, adult.id, body.opponent_id, str(count)),
        (adult.level, rival.level),
    )
    won = result["winner"] == 0
    bout = SumoBout(
        user_id=user.id,
        adult_id=adult.id,
        opponent_id=opponent_id,
        opponent_name=rival.name,
        game_day=day,
        daily_index=count,
        won=won,
        reward=10 if won else 3,
        replay=result,
        created_at=now,
    )
    session.add(bout)
    await session.flush()
    await reward(session, user.id, "shizuku", bout.reward, "sumo_bout", bout.id)
    return BoutReplay.model_validate(bout, from_attributes=True)


@router.get("/bouts")
async def history(user: CurrentUser, session: Session) -> list[BoutSummary]:
    return [
        BoutSummary.model_validate(bout, from_attributes=True)
        for bout in await _history(session, user.id)
    ]


@router.get("/bouts/{bout_id}")
async def replay(bout_id: str, user: CurrentUser, session: Session) -> BoutReplay:
    bout = await session.get(SumoBout, bout_id)
    if bout is None or bout.user_id != user.id:
        raise APIError("not_found", "取組が見つかりません", 404)
    return BoutReplay.model_validate(bout, from_attributes=True)
