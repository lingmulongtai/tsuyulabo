from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from tsuyulabo_api.auth.dependencies import get_current_user
from tsuyulabo_api.db.users import User
from tsuyulabo_api.services.clock import Clock, clock_payload, get_clock

router = APIRouter(prefix="/v1")


@router.get("/clock")
async def read_clock(
    user: Annotated[User, Depends(get_current_user)], clock: Annotated[Clock, Depends(get_clock)]
) -> dict[str, str | int]:
    return clock_payload(clock, user)
