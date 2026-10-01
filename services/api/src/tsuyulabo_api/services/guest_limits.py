from __future__ import annotations

from fastapi import Request
from tsuyulabo_api.services.client_ip import client_ip
from tsuyulabo_api.services.ratelimit import Limit
from tsuyulabo_api.services.request_limits import reject_rate


async def check_guest(request: Request) -> None:
    limiter = getattr(request.app.state, "rate_limiter", None)
    settings = request.app.state.settings
    if limiter is None or not settings.rate_limits_enabled:
        return
    reject_rate(
        await limiter.check(
            [
                Limit(f"guest:ip:{client_ip(request)}", settings.rate_guest_hour, 3600),
                Limit("guest:global:day", settings.rate_guest_day_global, 86400),
            ],
            # One global counter bounds memory even if an attacker rotates spoofed IPs.
            [Limit("guest:fallback:global", settings.rate_guest_fallback_hour_global, 3600)],
        )
    )
