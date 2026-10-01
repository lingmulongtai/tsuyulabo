from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from sqlalchemy import func, select
from tsuyulabo_api.db.models import Job, User
from tsuyulabo_api.errors import APIError
from tsuyulabo_api.routers import brain, shiori
from tsuyulabo_api.services.jobs import BrainClient, create_job, finish_job
from tsuyulabo_api.settings import Settings

from .adult_fixtures import make_adult
from .game_support import GameClient


async def test_global_admission_is_atomic_across_users(sessions: Any) -> None:
    sessions.configure(info={"guard_settings": Settings(job_max_total=1, _env_file=None)})
    async with sessions() as session, session.begin():
        session.add_all(
            [
                User(id="a", display_name="a", friend_code="aaaa"),
                User(id="b", display_name="b", friend_code="bbbb"),
            ]
        )

    async def submit(owner: str) -> bool:
        try:
            async with sessions() as session, session.begin():
                await create_job(session, owner, "brain.experiment")
            return True
        except APIError as exc:
            assert exc.code == "server_busy"
            return False

    assert sum(await asyncio.gather(submit("a"), submit("b"))) == 1


@pytest.mark.parametrize("path", ["shiori", "brain"])
async def test_api_busy_does_not_enqueue_or_cache_and_completion_frees_capacity(
    sessions: Any, path: str
) -> None:
    sessions.configure(info={"guard_settings": Settings(job_max_per_user=1, _env_file=None)})
    async with GameClient(sessions, shiori.router, brain.router) as game:
        queue = AsyncMock()
        game.app.state.job_queue = queue
        if path == "brain":
            adult = await make_adult(sessions, game)
            url, body = f"/v1/flies/{adult}/experiments", {}
        else:
            url, body = "/v1/shiori/ask", {"question": "なぜ？"}
        first = await game.post(url, body)
        assert first.status_code == 202, first.text
        key = str(uuid4())
        busy = await game.post(url, body, key)
        assert busy.status_code == 503, busy.text
        assert busy.json()["error"]["code"] == "server_busy"
        assert busy.headers["retry-after"] == "10"
        assert queue.enqueue.await_count == 1
        async with sessions() as session, session.begin():
            assert await session.scalar(select(func.count()).select_from(Job)) == 1
            job = await session.get(Job, first.json()["job_id"])
            job.status = "running"
        assert (await game.post(url, body, key)).status_code == 503
        async with sessions() as session, session.begin():
            job = await session.get(Job, first.json()["job_id"])
            await finish_job(session, job, result={})
        assert (await game.post(url, body, key)).status_code == 202
        assert queue.enqueue.await_count == 2


async def test_rollback_and_enqueue_failure_release_capacity(sessions: Any) -> None:
    sessions.configure(info={"guard_settings": Settings(job_max_total=1, _env_file=None)})
    async with sessions() as session, session.begin():
        session.add(User(id="u", display_name="u", friend_code="code"))
    async with sessions() as session, session.begin():
        await create_job(session, "u", "brain.training")
        await session.rollback()
    queue = AsyncMock()
    queue.enqueue.side_effect = ConnectionError("down")
    client = BrainClient(sessions, queue)
    assert (await client.submit("u", "brain.training", {})).status == "failed"
    assert (await client.submit("u", "shiori.answer", {})).status == "failed"
