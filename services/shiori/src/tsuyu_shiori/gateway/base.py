from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Protocol


@dataclass(frozen=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(frozen=True)
class Cost:
    input_tokens: int = 0
    output_tokens: int = 0
    usd: float = 0.0
    cached: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Response:
    text: str = ""
    tool_calls: list[ToolCall] = field(default_factory=list)
    cost: Cost = field(default_factory=Cost)
    # Keep provider-native output (including reasoning items) for tool continuation.
    continuation: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Response:
        return cls(
            data["text"],
            [ToolCall(**call) for call in data["tool_calls"]],
            Cost(**data["cost"]),
            data.get("continuation", []),
        )


class Provider(Protocol):
    @property
    def cache_namespace(self) -> str: ...

    def model_for(self, purpose: str) -> str: ...

    async def complete(
        self, messages: list[dict[str, Any]], tools: list[dict[str, Any]], model: str
    ) -> Response: ...
