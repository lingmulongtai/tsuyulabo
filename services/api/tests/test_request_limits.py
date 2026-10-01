from __future__ import annotations

from typing import Any

import pytest
from tsuyulabo_api.routers import brain, daily_circuit, friends, puzzles, shiori
from tsuyulabo_api.services.ratelimit import MemoryCounter, RateLimiter
from tsuyulabo_api.services.request_limits import user_limits
from tsuyulabo_api.settings import Settings

from .game_support import GameClient


@pytest.mark.parametrize(
    ("path", "method", "bucket", "count"),
    [
        ("/v1/shiori/ask", "POST", "shiori:minute", 10),
        ("/v1/shiori/memo", "GET", "all", 300),
        ("/v1/flies/a/behavior", "GET", "brain", 20),
        ("/v1/flies/a/brain/activity", "GET", "brain", 20),
        ("/v1/flies/a/experiments", "POST", "brain", 20),
        ("/v1/puzzles/a/submit", "POST", "puzzle", 60),
        ("/v1/daily-circuit/start", "POST", "puzzle", 60),
        ("/v1/friends/a/lab", "GET", "friends", 30),
        ("/v1/home", "GET", "all", 300),
    ],
)
def test_route_buckets(path: str, method: str, bucket: str, count: int) -> None:
    rules = user_limits(path, method, "u", Settings(_env_file=None))
    assert any(rule.key == f"user:u:{bucket}" and rule.count == count for rule in rules)


@pytest.mark.parametrize(
    ("path", "method", "field"),
    [
        ("/v1/flies/missing/behavior", "GET", "rate_brain_minute"),
        ("/v1/flies/missing/brain/activity", "GET", "rate_brain_minute"),
        ("/v1/shiori/ask", "POST", "rate_shiori_minute"),
        ("/v1/puzzles", "POST", "rate_puzzle_minute"),
        ("/v1/daily-circuit/start", "POST", "rate_puzzle_minute"),
        ("/v1/friends/missing/lab", "GET", "rate_friends_minute"),
        ("/v1/me", "GET", "rate_authenticated_minute"),
    ],
)
async def test_representative_routes_429(sessions: Any, path: str, method: str, field: str) -> None:
    async with GameClient(
        sessions, brain.router, shiori.router, puzzles.router, daily_circuit.router, friends.router
    ) as game:
        now = [100.0]
        game.app.state.settings = Settings(**{field: 1}, _env_file=None)
        game.app.state.rate_limiter = RateLimiter(MemoryCounter(lambda: now[0]))
        # Invalid resources/bodies still consume one request; no expensive work required.
        first = await (game.get(path) if method == "GET" else game.post(path))
        assert first.status_code != 429
        second = await (game.get(path) if method == "GET" else game.post(path))
        assert second.status_code == 429, second.text
        assert second.headers["retry-after"] == "20"
        assert second.json()["error"]["details"] == {"retry_after": 20}
        now[0] = 120
        assert (await (game.get(path) if method == "GET" else game.post(path))).status_code != 429


async def test_mutation_auth_is_not_double_counted_and_disabled_limits(sessions: Any) -> None:
    async with GameClient(sessions) as game:
        counter = MemoryCounter(lambda: 100)
        game.app.state.settings = Settings(rate_authenticated_minute=1, _env_file=None)
        game.app.state.rate_limiter = RateLimiter(counter)
        assert (
            await game.client.patch(
                "/v1/me",
                json={"display_name": "new"},
                headers=game.headers | {"Idempotency-Key": "00000000-0000-0000-0000-000000000001"},
            )
        ).status_code == 200
        game.app.state.settings.rate_limits_enabled = False
        assert (await game.get("/v1/me")).status_code == 200
