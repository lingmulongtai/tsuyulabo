from __future__ import annotations

import json
from copy import deepcopy
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

from httpx import ASGITransport, AsyncClient
from tsuyulabo_api.brain_adapter import BrainAdapter
from tsuyulabo_api.domain.clock import JST
from tsuyulabo_api.routers import dev, users

from .http_support import router_app


@dataclass
class FakeState:
    params: dict
    values: dict

    def to_bytes(self) -> bytes:
        return json.dumps(asdict(self)).encode()

    @classmethod
    def from_bytes(cls, value: bytes) -> FakeState:
        return cls(**json.loads(value))


class FakeFacade:
    FlyState = FakeState

    def default_params(self) -> dict:
        return {}

    def generate_individual(self, **kwargs: Any) -> dict:
        return kwargs

    def new_fly_state(self, params: dict) -> FakeState:
        return FakeState(params, {})

    def apply_training(
        self, state: FakeState, cue: str, valence: str, strength: float, seed: int
    ) -> tuple:
        state = deepcopy(state)
        value = max(
            -1, min(1, state.values.get(cue, 0) + strength * (1 if valence == "reward" else -1))
        )
        state.values[cue] = value
        return state, value

    def preference_index(self, state: dict, cue: str, seed: int, trials: int) -> float:
        return state.values.get(cue, 0)

    def predict_behavior(self, state: dict, context: dict) -> dict:
        return {"walk": 0.75, "rest": 0.25}

    def run_odor_choice(self, state: dict, cue: str, trials: int, seed: int) -> dict:
        toward = round(trials * (1 + state.values.get(cue, 0)) / 2)
        return {"toward": toward, "away": trials - toward}


class FakeBrain(BrainAdapter):
    @property
    def api(self) -> FakeFacade:
        return FakeFacade()


class TestClock:
    __test__ = False

    def __init__(self) -> None:
        self.value = datetime(2026, 1, 5, 4, tzinfo=JST)

    def now(self) -> datetime:
        return self.value

    def advance(self, seconds: float) -> None:
        self.value += timedelta(seconds=seconds)


class GameClient:
    def __init__(self, sessions: Any, *routers: Any) -> None:
        self.app = router_app(sessions, users.router, dev.router, *routers)
        self.clock = TestClock()
        self.app.state.clock = self.clock
        self.app.state.brain_adapter = FakeBrain()
        self.client = AsyncClient(transport=ASGITransport(app=self.app), base_url="http://test")
        self.headers: dict[str, str] = {}
        self.user: dict = {}

    async def __aenter__(self) -> GameClient:
        await self.client.__aenter__()
        guest = await self.post("/v1/auth/guest", {"display_name": "???"})
        self.headers = {"Authorization": f"Bearer {guest.json()['token']}"}
        self.user = guest.json()["user"]
        return self

    async def __aexit__(self, *args: Any) -> None:
        await self.client.__aexit__(*args)

    async def post(self, path: str, body: dict | None = None, key: str | None = None) -> Any:
        return await self.client.post(
            path, json=body, headers=self.headers | {"Idempotency-Key": key or str(uuid4())}
        )

    async def get(self, path: str) -> Any:
        return await self.client.get(path, headers=self.headers)

    async def advance(self, **body: Any) -> Any:
        response = await self.post("/v1/dev/time/advance", body)
        assert response.status_code == 200, response.text
        return response.json()
