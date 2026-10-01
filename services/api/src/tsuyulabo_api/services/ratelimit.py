"""Atomic fixed windows. All rules in one request are admitted together."""

from __future__ import annotations

import logging
import math
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

from redis.asyncio import Redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Limit:
    key: str
    count: int
    seconds: int


class Counter(Protocol):
    async def consume(self, limits: Sequence[Limit]) -> int:
        """Return seconds until admission, or zero when admitted."""
        ...


class MemoryCounter:
    """Injectable counter; no await between checking and updating on the app event loop."""

    def __init__(self, clock: Callable[[], float] = time.time) -> None:
        self.clock = clock
        self.windows: dict[str, tuple[float, int]] = {}

    async def consume(self, limits: Sequence[Limit]) -> int:
        now = self.clock()
        self.windows = {key: item for key, item in self.windows.items() if item[0] > now}
        retry = 0
        for rule in limits:
            end, count = self.windows.get(rule.key, (0, 0))
            if end > now and count >= rule.count:
                retry = max(retry, math.ceil(end - now))
        if retry:
            return retry
        for rule in limits:
            end = (now // rule.seconds + 1) * rule.seconds
            _, count = self.windows.get(rule.key, (end, 0))
            self.windows[rule.key] = (end, count + 1)
        return 0


SCRIPT = """
local now = tonumber(redis.call('TIME')[1])
local retry = 0
local keys = {}
local waits = {}
for i, key in ipairs(KEYS) do
    local count = tonumber(ARGV[i * 2 - 1])
    local seconds = tonumber(ARGV[i * 2])
    local window = math.floor(now / seconds)
    keys[i] = key .. ':' .. window
    waits[i] = seconds - now % seconds
    if tonumber(redis.call('GET', keys[i]) or '0') >= count then
        retry = math.max(retry, waits[i])
    end
end
if retry > 0 then return retry end
for i, key in ipairs(keys) do
    redis.call('INCR', key)
    redis.call('EXPIRE', key, waits[i])
end
return 0
"""


class RedisCounter:
    def __init__(self, redis: Redis) -> None:
        self.redis = redis

    async def consume(self, limits: Sequence[Limit]) -> int:
        if not limits:
            return 0
        return int(
            await self.redis.eval(
                SCRIPT,
                len(limits),
                *(f"tsuyu:rate:{rule.key}" for rule in limits),
                *(value for rule in limits for value in (rule.count, rule.seconds)),
            )
        )


class RateLimiter:
    def __init__(self, counter: Counter | None, fallback: Counter | None = None) -> None:
        self.counter = counter
        self.fallback = fallback or MemoryCounter()
        self.last_warning = -math.inf

    async def check(self, limits: Sequence[Limit], fallback: Sequence[Limit] = ()) -> int:
        try:
            if self.counter is None:
                raise ConnectionError("Redis is not configured")
            return await self.counter.consume(limits)
        except (RedisError, ConnectionError, OSError):
            # Bound log volume during outages; never log credentials or user/IP keys.
            now = time.monotonic()
            if now - self.last_warning >= 60:
                logger.warning("rate limiter Redis unavailable; guest fallback active, play open")
                self.last_warning = now
            return await self.fallback.consume(fallback) if fallback else 0
