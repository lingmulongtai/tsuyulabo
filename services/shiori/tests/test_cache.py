from __future__ import annotations

from typing import Any

from tsuyu_shiori.gateway.base import Cost, Response
from tsuyu_shiori.gateway.cache import CachedProvider, MemoryCache, RedisCache


class CountingProvider:
    cache_namespace = "counter"
    calls = 0

    def model_for(self, purpose: str) -> str:
        return purpose

    async def complete(self, messages: list, tools: list, model: str) -> Response:
        self.calls += 1
        return Response("answer", cost=Cost(10, 2, 0.01))


async def test_cache_key_hits_cost_and_lru() -> None:
    source = CountingProvider()
    provider = CachedProvider(source, MemoryCache(2))
    assert (await provider.complete([], [], "a")).cost.usd == 0.01
    assert (await provider.complete([], [], "a")).cost == Cost(cached=True)
    await provider.complete([], [], "b")
    await provider.complete([], [], "a")
    await provider.complete([], [], "c")
    await provider.complete([], [], "b")
    assert source.calls == 4
    await provider.complete([], [{"name": "new"}], "b")
    assert source.calls == 5


async def test_redis_serialization_without_server() -> None:
    class FakeRedis:
        values: dict[str, str] = {}

        async def get(self, key: str) -> str | None:
            return self.values.get(key)

        async def set(self, key: str, value: str, *, ex: int) -> Any:
            assert ex == 3600
            self.values[key] = value

    cache = RedisCache(FakeRedis())
    assert await cache.get("missing") is None
    response = Response("result", cost=Cost(7, 8, 0.2))
    await cache.put("key", response)
    assert await cache.get("key") == response
