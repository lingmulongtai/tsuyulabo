from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Protocol

from fastapi import Request
from tsuyulabo_api.db.users import User
from tsuyulabo_api.domain.clock import slot_of


class Clock(Protocol):
    def now(self) -> datetime: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


def get_clock(request: Request) -> Clock:
    return request.app.state.clock


def game_now(clock: Clock, user: User) -> datetime:
    return clock.now().astimezone(UTC) + timedelta(seconds=user.dev_time_offset_s)


def clock_payload(clock: Clock, user: User) -> dict[str, str | int]:
    server = clock.now().astimezone(UTC)
    game = server + timedelta(seconds=user.dev_time_offset_s)
    return {
        "server_now": server.isoformat(),
        "game_now": game.isoformat(),
        "tz": "Asia/Tokyo",
        "slot": slot_of(game),
        "day_boundary_hour": 4,
    }
