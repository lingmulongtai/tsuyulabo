from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest
from redis.exceptions import ConnectionError as RedisConnectionError
from tsuyulabo_api.services.ratelimit import Limit, MemoryCounter, RateLimiter, RedisCounter


async def test_windows_isolation_retry_and_rollover() -> None:
    now = [58.1]
    counter = MemoryCounter(lambda: now[0])
    assert await counter.consume([Limit("a", 1, 60)]) == 0
    assert await counter.consume([Limit("a", 1, 60)]) == 2
    assert await counter.consume([Limit("b", 1, 60)]) == 0
    now[0] = 60
    assert await counter.consume([Limit("a", 1, 60)]) == 0
    assert "b" not in counter.windows


async def test_all_rules_atomic_and_concurrent() -> None:
    counter = MemoryCounter(lambda: 100)
    assert await counter.consume([Limit("daily", 1, 86400)]) == 0
    assert await counter.consume([Limit("minute", 2, 60), Limit("daily", 1, 86400)]) > 0
    assert "minute" not in counter.windows
    results = await asyncio.gather(*(counter.consume([Limit("race", 2, 60)]) for _ in range(10)))
    assert results.count(0) == 2


async def test_redis_arguments_and_retry() -> None:
    redis = AsyncMock()
    redis.eval.return_value = 23
    assert await RedisCounter(redis).consume([Limit("user:a", 2, 60)]) == 23
    args = redis.eval.call_args.args
    assert args[1:] == (1, "tsuyu:rate:user:a", 2, 60)


@pytest.mark.parametrize("redis_down", [True, False])
async def test_down_plays_open_and_guests_have_bounded_fallback(redis_down: bool, caplog) -> None:
    counter = AsyncMock()
    counter.consume.side_effect = RedisConnectionError("private")
    limiter = RateLimiter(counter if redis_down else None, MemoryCounter(lambda: 100))
    assert await limiter.check([Limit("play", 1, 60)]) == 0
    fallback = [Limit("guest:global", 1, 3600)]
    assert await limiter.check([Limit("guest:ip", 5, 3600)], fallback) == 0
    assert await limiter.check([Limit("guest:other", 5, 3600)], fallback) == 3500
    assert "guest fallback active" in caplog.text
    assert "private" not in caplog.text


async def test_available_redis_enforces_limit_without_fallback() -> None:
    counter = MemoryCounter(lambda: 100)
    limiter = RateLimiter(counter)
    assert await limiter.check([Limit("play", 1, 60)]) == 0
    assert await limiter.check([Limit("play", 1, 60)]) == 20
