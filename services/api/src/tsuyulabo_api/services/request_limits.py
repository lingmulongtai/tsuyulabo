from __future__ import annotations

from fastapi import Request
from tsuyulabo_api.errors import APIError
from tsuyulabo_api.services.ratelimit import Limit
from tsuyulabo_api.settings import Settings


def user_limits(path: str, method: str, user_id: str, settings: Settings) -> list[Limit]:
    rules = [Limit(f"user:{user_id}:all", settings.rate_authenticated_minute, 60)]
    if path.startswith("/v1/shiori/") and method == "POST":
        rules += [
            Limit(f"user:{user_id}:shiori:minute", settings.rate_shiori_minute, 60),
            Limit(f"user:{user_id}:shiori:day", settings.rate_shiori_day, 86400),
        ]
    elif path.startswith("/v1/flies/") and path.endswith(
        ("/experiments", "/behavior", "/brain/activity")
    ):
        rules.append(Limit(f"user:{user_id}:brain", settings.rate_brain_minute, 60))
    elif path.startswith(("/v1/puzzles", "/v1/daily-circuit")):
        rules.append(Limit(f"user:{user_id}:puzzle", settings.rate_puzzle_minute, 60))
    elif path.startswith("/v1/friends"):
        rules.append(Limit(f"user:{user_id}:friends", settings.rate_friends_minute, 60))
    return rules


def reject_rate(retry: int) -> None:
    if retry:
        raise APIError(
            "rate_limited",
            "少し時間をおいてから、もう一度ためしてね",
            429,
            {"retry_after": retry},
        )


async def check_user(request: Request, user_id: str) -> None:
    limiter = getattr(request.app.state, "rate_limiter", None)
    if limiter is None or not request.app.state.settings.rate_limits_enabled:
        return
    if getattr(request.state, "rate_checked", False):
        return
    reject_rate(
        await limiter.check(
            user_limits(
                request.url.path,
                request.method,
                user_id,
                request.app.state.settings,
            )
        )
    )
    request.state.rate_checked = True
