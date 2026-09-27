from __future__ import annotations

import hashlib
import json
from collections import OrderedDict
from copy import deepcopy
from dataclasses import replace
from typing import Any, Protocol

from .base import Cost, Provider, Response


class Cache(Protocol):
    async def get(self, key: str) -> Response | None: ...

    async def put(self, key: str, value: Response) -> None: ...


class MemoryCache:
    def __init__(self, capacity: int = 128) -> None:
        if capacity < 1:
            raise ValueError("capacity must be positive")
        self.capacity = capacity
        self.entries: OrderedDict[str, Response] = OrderedDict()

    async def get(self, key: str) -> Response | None:
        if key not in self.entries:
            return None
        self.entries.move_to_end(key)
        return deepcopy(self.entries[key])

    async def put(self, key: str, value: Response) -> None:
        self.entries[key] = deepcopy(value)
        self.entries.move_to_end(key)
        while len(self.entries) > self.capacity:
            self.entries.popitem(last=False)


class RedisClient(Protocol):
    async def get(self, key: str) -> bytes | str | None: ...

    async def set(self, key: str, value: str, *, ex: int) -> object: ...


class RedisCache:
    """Inject a redis.asyncio client; Shiori does not require Redis to be installed."""

    def __init__(self, client: RedisClient, ttl: int = 3600) -> None:
        self.client, self.ttl = client, ttl

    async def get(self, key: str) -> Response | None:
        value = await self.client.get("shiori:v1:" + key)
        return Response.from_dict(json.loads(value)) if value else None

    async def put(self, key: str, value: Response) -> None:
        await self.client.set("shiori:v1:" + key, json.dumps(value.to_dict()), ex=self.ttl)


class CachedProvider:
    def __init__(self, provider: Provider, cache: Cache | None = None) -> None:
        self.provider, self.cache = provider, cache if cache is not None else MemoryCache()

    @property
    def cache_namespace(self) -> str:
        return self.provider.cache_namespace

    def model_for(self, purpose: str) -> str:
        return self.provider.model_for(purpose)

    async def complete(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]], model: str
    ) -> Response:
        payload = [self.cache_namespace, model, messages, tools]
        key = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        result = await self.cache.get(key)
        if result is not None:
            return replace(result, cost=Cost(cached=True))
        result = await self.provider.complete(messages, tools, model)
        await self.cache.put(key, result)
        return result
