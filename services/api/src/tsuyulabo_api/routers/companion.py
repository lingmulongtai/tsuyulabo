"""Owned individual diary, quiet hints and contextual why; no chat surface."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from tsuyulabo_api.db.models import Adult, Week
from tsuyulabo_api.errors import APIError
from tsuyulabo_api.services import behaviour_why, diary, quiet_hint
from tsuyulabo_api.services.clock import game_now
from tsuyulabo_api.services.game import CurrentClock, CurrentUser, Session
from tsuyulabo_api.services.idempotency import IdempotentRoute

router = APIRouter(route_class=IdempotentRoute)


class DiaryMoment(BaseModel):
    record_id: str
    at: str
    seed: str | None
    stage: str
    behaviour: str
    environment: dict[str, Any]
    sex: Literal["f", "m"] | None = None
    phenotypes: list[str] = []


class DiaryResponse(BaseModel):
    id: str
    week_id: str
    day: str
    text: str
    evidence: list[str]
    snapshot: DiaryMoment
    ai_label: str = "AI"


class IndividualResponse(BaseModel):
    id: str
    name: str


class HintResponse(BaseModel):
    id: str
    text: str
    evidence: list[str]
    ai_label: str = "AI"


class WhyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source: Literal["brain_decoder", "copy_odor_choice"] = "brain_decoder"
    behaviour: (
        Literal[
            "rest",
            "walk",
            "feed",
            "groom",
            "approach",
            "avoid",
            "escape",
            "turn_left",
            "turn_right",
            "fly",
        ]
        | None
    ) = None


class WhyResponse(BaseModel):
    text: str
    evidence: list[str]
    ai_label: str
    disclaimer: str
    observation_id: str


@router.get("/individuals", response_model=list[IndividualResponse])
async def individuals(user: CurrentUser, session: Session) -> list[dict[str, str]]:
    rows = await session.execute(
        select(Week, Adult)
        .outerjoin(Adult, Adult.week_id == Week.id)
        .where(
            Week.user_id == user.id,
        )
        .order_by(Week.started_at.desc())
    )
    return [
        {
            "id": adult.id if adult else week.id,
            "name": adult.name if adult else f"{week.started_at.date()}に迎えた子",
        }
        for week, adult in rows
    ]


@router.get("/diary", response_model=list[DiaryResponse])
async def read_diary(fly_id: str, user: CurrentUser, session: Session) -> list[dict[str, Any]]:
    try:
        return await diary.history(session, user.id, fly_id)
    except ValueError as exc:
        raise APIError("not_found", "この子の日記が見つかりません", 404) from exc


@router.get("/flies/{fly_id}/hint", response_model=HintResponse | None)
async def read_hint(
    fly_id: str,
    user: CurrentUser,
    session: Session,
    clock: CurrentClock,
) -> dict[str, Any] | None:
    try:
        return await quiet_hint.current(session, user.id, fly_id, game_now(clock, user))
    except ValueError as exc:
        raise APIError("not_found", "この子が見つかりません", 404) from exc


@router.post("/hints/{hint_id}/dismiss")
async def dismiss_hint(
    hint_id: str,
    user: CurrentUser,
    session: Session,
    clock: CurrentClock,
) -> dict[str, bool]:
    try:
        await quiet_hint.dismiss(session, user.id, hint_id, game_now(clock, user))
    except ValueError as exc:
        raise APIError("not_found", "ヒントが見つかりません", 404) from exc
    return {"dismissed": True}


@router.post("/flies/{fly_id}/why", response_model=WhyResponse)
async def why(
    fly_id: str,
    body: WhyRequest,
    user: CurrentUser,
    session: Session,
    clock: CurrentClock,
) -> dict[str, Any]:
    from tsuyulabo_api.services.shiori_store import SQLRecordStore

    try:
        await SQLRecordStore(session, user.id).fly_week(fly_id)
    except ValueError as exc:
        raise APIError("not_found", "この子が見つかりません", 404) from exc
    try:
        return await behaviour_why.explain(
            session,
            user.id,
            fly_id,
            game_now(clock, user),
            behaviour=body.behaviour,
            source=body.source,
        )
    except ValueError as exc:
        raise APIError(
            "behaviour_changed", "動きが変わりました。もう一度この子を選んでください", 409
        ) from exc
