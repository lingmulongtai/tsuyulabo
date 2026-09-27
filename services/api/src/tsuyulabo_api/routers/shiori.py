from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Request
from pydantic import BaseModel, ConfigDict, Field
from tsuyulabo_api.services import memo
from tsuyulabo_api.services.clock import game_now
from tsuyulabo_api.services.dispatch import enqueue
from tsuyulabo_api.services.game import CurrentClock, CurrentUser, Session
from tsuyulabo_api.services.idempotency import IdempotentRoute

router = APIRouter(prefix="/v1/shiori", route_class=IdempotentRoute)


class AskRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    question: str = Field(min_length=1, max_length=2000)


@router.get("/memo")
async def read_memo(
    user: CurrentUser, session: Session, clock: CurrentClock
) -> dict[str, Any] | None:
    return await memo.today(session, user.id, game_now(clock, user))


@router.post("/ask", status_code=202)
async def ask(
    body: AskRequest,
    request: Request,
    tasks: BackgroundTasks,
    user: CurrentUser,
    session: Session,
    clock: CurrentClock,
) -> dict[str, str]:
    job = await enqueue(
        session,
        request,
        tasks,
        user.id,
        "shiori.answer",
        {
            "user_id": user.id,
            "question": body.question,
            "game_now": game_now(clock, user).isoformat(),
        },
    )
    return {"job_id": job.id}
