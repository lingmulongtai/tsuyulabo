"""Run Lua integration coverage with uv run --with 'fakeredis[lua]' pytest this_file."""

from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest
from tsuyulabo_api.services.ratelimit import Limit, RedisCounter

fakeredis = pytest.importorskip("fakeredis.aioredis")


async def test_lua_atomic_windows_ttl_isolation_and_shared_processes() -> None:
    server = fakeredis.FakeServer()
    redis = fakeredis.FakeRedis(server=server)
    other = fakeredis.FakeRedis(server=server)
    try:
        counter = RedisCounter(redis)
        with patch("time.time", return_value=100):
            assert await counter.consume([Limit("daily", 1, 86400)]) == 0
            assert (
                await counter.consume([Limit("minute", 2, 60), Limit("daily", 1, 86400)]) == 86300
            )
            assert not await redis.exists("tsuyu:rate:minute:1")
            rules = [Limit("race", 2, 60)]
            results = await asyncio.gather(
                *((counter if i % 2 else RedisCounter(other)).consume(rules) for i in range(10))
            )
            assert results.count(0) == 2
            assert results.count(20) == 8
            assert await redis.ttl("tsuyu:rate:race:1") == 20
            assert await counter.consume([Limit("separate", 1, 60)]) == 0
        with patch("time.time", return_value=120.1):
            assert await counter.consume(rules) == 0
            assert not await redis.exists("tsuyu:rate:race:1")
            assert await redis.ttl("tsuyu:rate:race:2") == 60
    finally:
        await redis.aclose()
        await other.aclose()
