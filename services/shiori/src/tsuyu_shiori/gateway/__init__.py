from __future__ import annotations

import os

from .base import Cost, Provider, Response, ToolCall
from .cache import CachedProvider, MemoryCache, RedisCache
from .http import AnthropicProvider, OpenAIProvider
from .mock import MockProvider

__all__ = [
    "AnthropicProvider",
    "CachedProvider",
    "Cost",
    "MemoryCache",
    "MockProvider",
    "OpenAIProvider",
    "Provider",
    "RedisCache",
    "Response",
    "ToolCall",
    "default_provider",
]


def default_provider() -> Provider:
    name = os.getenv("SHIORI_PROVIDER", "mock").lower()
    providers = {"mock": MockProvider, "anthropic": AnthropicProvider, "openai": OpenAIProvider}
    if name not in providers:
        raise ValueError("SHIORI_PROVIDER must be mock, anthropic, or openai")
    return CachedProvider(providers[name]())
