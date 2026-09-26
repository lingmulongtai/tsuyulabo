from __future__ import annotations

import math
from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import Annotated, Literal, Self

from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tsuyulabo_api.auth.dependencies import get_current_user
from tsuyulabo_api.db.session import get_session
from tsuyulabo_api.db.users import User
from tsuyulabo_api.errors import APIError
from tsuyulabo_api.services.clock import Clock, clock_payload, game_now, get_clock
from tsuyulabo_api.services.idempotency import IdempotentRoute
from tsuyulabo_api.services.timeutil import next_boundary


class DevRoute(IdempotentRoute):
    def get_route_handler(self) -> Callable[[Request], Awaitable[Response]]:
        original = super().get_route_handler()

        async def handle(request: Request) -> Response:
            # Check before replay as well: disabling dev tools revokes all dev access.
            if not request.app.state.settings.dev_tools:
                raise APIError("dev_tools_disabled", "開発ツールは無効です", 403)
            return await original(request)

        return handle


router = APIRouter(prefix="/v1/dev/time", route_class=DevRoute)
CurrentUser = Annotated[User, Depends(get_current_user)]
Session = Annotated[AsyncSession, Depends(get_session)]
CurrentClock = Annotated[Clock, Depends(get_clock)]


class AdvanceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)
    hours: float | None = Field(default=None, gt=0)
    to: Literal["next_slot", "next_day"] | None = None

    @model_validator(mode="after")
    def exactly_one_target(self) -> Self:
        if (self.hours is None) == (self.to is None):
            raise ValueError("provide exactly one of hours or to")
        return self


def dev_payload(clock: Clock, user: User) -> dict[str, str | int]:
    return clock_payload(clock, user) | {"dev_time_offset_s": user.dev_time_offset_s}


@router.get("")
async def read_time(user: CurrentUser, clock: CurrentClock) -> dict[str, str | int]:
    return dev_payload(clock, user)


@router.post("/advance")
async def advance_time(
    body: AdvanceRequest, user: CurrentUser, session: Session, clock: CurrentClock
) -> dict[str, str | int]:
    await session.scalar(
        select(User)
        .where(User.id == user.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    now = game_now(clock, user)
    try:
        seconds = (
            math.ceil(body.hours * 3600)
            if body.hours is not None
            else math.ceil((next_boundary(now, body.to) - now).total_seconds())
        )
        now + timedelta(seconds=seconds)
    except (ValueError, OverflowError) as exc:
        raise APIError("validation_error", "指定した日時が範囲外です", 422) from exc
    user.dev_time_offset_s += seconds
    await session.flush()
    return dev_payload(clock, user)


@router.post("/reset")
async def reset_time(
    user: CurrentUser, session: Session, clock: CurrentClock
) -> dict[str, str | int]:
    await session.scalar(
        select(User)
        .where(User.id == user.id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    user.dev_time_offset_s = 0
    await session.flush()
    return dev_payload(clock, user)
