from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field, StrictInt
from sqlalchemy import and_, or_, select
from tsuyulabo_api.db.models import Adult, DailyCircuitAttempt, Friendship, User
from tsuyulabo_api.db.operations import insert_if_absent
from tsuyulabo_api.domain.clock import day_start, game_day
from tsuyulabo_api.domain.puzzles import daily_circuit, training
from tsuyulabo_api.domain.puzzles.common import verify_wall_clock
from tsuyulabo_api.errors import APIError
from tsuyulabo_api.services.game import CurrentClock, CurrentUser, Session, reward
from tsuyulabo_api.services.idempotency import IdempotentRoute

router = APIRouter(prefix="/v1/daily-circuit", route_class=IdempotentRoute)


class DailyCheckpoint(BaseModel):
    cell: int
    k: int


class DailyCircuitParams(BaseModel):
    n: Literal[7]
    checkpoints: list[DailyCheckpoint]
    cue: Literal["banana"]
    valence: Literal["reward"]


class DailyAttempt(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    started_at: datetime
    expires_at: datetime


class DailyResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    day: date
    elapsed_ms: int
    shizuku: int
    submitted_at: datetime


class DailyCircuitResponse(BaseModel):
    day: date
    params: DailyCircuitParams
    server_now: datetime
    resets_at: datetime
    attempt: DailyAttempt | None
    my_result: DailyResult | None


class DailyStartRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    day: date


class DailySubmitRequest(DailyStartRequest):
    path: list[StrictInt] = Field(min_length=49, max_length=49)
    elapsed_ms: int = Field(ge=0, le=600_000, strict=True)


class DailyAvatar(BaseModel):
    strain: Literal["wild", "white", "yellow", "ebony", "curly", "vestigial"]
    sex: Literal["m", "f"]


class DailyRankingEntry(BaseModel):
    rank: int
    user_id: str
    display_name: str
    is_me: bool
    elapsed_ms: int
    submitted_at: datetime
    avatar: DailyAvatar


class DailyRanking(BaseModel):
    day: date
    entries: list[DailyRankingEntry]


def require_today(day: date, now: datetime) -> None:
    if day != game_day(now):
        raise APIError("puzzle_expired", "今日の問題に切り替わりました", 409)


async def daily_payload(user: User, session: Session, now: datetime) -> DailyCircuitResponse:
    day = game_day(now)
    attempt = await session.get(DailyCircuitAttempt, (user.id, day))
    params, _ = daily_circuit.generate(day)
    return DailyCircuitResponse(
        day=day,
        params=DailyCircuitParams.model_validate(params),
        server_now=now,
        resets_at=day_start(day + timedelta(days=1)),
        attempt=DailyAttempt.model_validate(attempt) if attempt else None,
        my_result=(
            DailyResult.model_validate(attempt)
            if attempt and attempt.submitted_at is not None
            else None
        ),
    )


@router.get("")
async def today(user: CurrentUser, session: Session, clock: CurrentClock) -> DailyCircuitResponse:
    return await daily_payload(user, session, clock.now())


@router.post("/start")
async def start(
    body: DailyStartRequest, user: CurrentUser, session: Session, clock: CurrentClock
) -> DailyCircuitResponse:
    now = clock.now().astimezone(UTC)
    require_today(body.day, now)
    await insert_if_absent(
        session,
        DailyCircuitAttempt,
        {
            "user_id": user.id,
            "day": body.day,
            "started_at": now,
            "expires_at": min(now + timedelta(minutes=10), day_start(body.day + timedelta(days=1))),
        },
        ["user_id", "day"],
    )
    return await daily_payload(user, session, now)


@router.post("/submit")
async def submit(
    body: DailySubmitRequest, user: CurrentUser, session: Session, clock: CurrentClock
) -> DailyResult:
    now = clock.now().astimezone(UTC)
    require_today(body.day, now)
    # CurrentUser locks serialize different keys; the composite PK also protects starts.
    attempt = await session.get(DailyCircuitAttempt, (user.id, body.day))
    if attempt is None:
        raise APIError("not_found", "先に今日の回路を開始してください", 404)
    if attempt.submitted_at is not None:
        return DailyResult.model_validate(attempt)
    if now >= attempt.expires_at:
        raise APIError("puzzle_expired", "本番の時間が終わりました。練習で遊べます", 409)
    params, _ = daily_circuit.generate(body.day)
    verified = training.verify(params, body.model_dump())
    if verified.valid:
        verified = verify_wall_clock(attempt.started_at, now, body.elapsed_ms)
    if not verified.valid:
        raise APIError("invalid_submission", "操作記録が不正です", 422, {"reason": verified.reason})
    attempt.elapsed_ms = max(
        body.elapsed_ms, int((now - attempt.started_at).total_seconds() * 1000)
    )
    attempt.shizuku = daily_circuit.shizuku_for(attempt.elapsed_ms)
    attempt.submitted_at = now
    await reward(
        session, user.id, "shizuku", attempt.shizuku, "daily_circuit", f"{user.id}:{body.day}"
    )
    await session.flush()
    return DailyResult.model_validate(attempt)


@router.get("/ranking")
async def ranking(user: CurrentUser, session: Session, clock: CurrentClock) -> DailyRanking:
    day = game_day(clock.now())
    friend_ids = select(Friendship.friend_id).where(Friendship.user_id == user.id)
    rows = await session.execute(
        select(DailyCircuitAttempt, User, Adult)
        .join(User, DailyCircuitAttempt.user_id == User.id)
        .outerjoin(Adult, and_(Adult.id == User.favorite_adult_id, Adult.user_id == User.id))
        .where(
            DailyCircuitAttempt.day == day,
            DailyCircuitAttempt.submitted_at.is_not(None),
            or_(User.id == user.id, User.id.in_(friend_ids)),
        )
        .order_by(DailyCircuitAttempt.elapsed_ms, DailyCircuitAttempt.submitted_at, User.id)
    )
    return DailyRanking(
        day=day,
        entries=[
            DailyRankingEntry(
                rank=index,
                user_id=person.id,
                display_name=person.display_name,
                is_me=person.id == user.id,
                elapsed_ms=attempt.elapsed_ms,
                submitted_at=attempt.submitted_at,
                avatar=DailyAvatar(
                    strain=adult.strain if adult else "wild", sex=adult.sex if adult else "f"
                ),
            )
            for index, (attempt, person, adult) in enumerate(rows, 1)
        ],
    )
