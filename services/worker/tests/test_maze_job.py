from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tsuyu_worker.jobs import run_job
from tsuyulabo_api.brain_adapter import BrainAdapter
from tsuyulabo_api.db.models import Job, User
from tsuyulabo_api.domain.maze import generate
from tsuyulabo_api.services.maze_race import simulate


async def test_maze_job_uses_frozen_inputs_and_redelivery_is_safe(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    params = {
        "maze": generate("2026-W39"),
        "placements": [],
        "seed": 42,
        "snapshot": BrainAdapter().new(),
    }
    async with sessions() as session, session.begin():
        user = User(display_name="racer", friend_code="RACE1234")
        session.add(user)
        await session.flush()
        job = Job(user_id=user.id, kind="brain.maze_run", status="pending", params=params)
        session.add(job)
        await session.flush()
        job_id = job.id
    expected = simulate(params)
    assert (
        await run_job(job_id, "brain.maze_run", sessions=sessions, params={"seed": 0}) == expected
    )
    assert await run_job(job_id, "brain.maze_run", sessions=sessions) == expected
    async with sessions() as session:
        job = await session.get(Job, job_id)
        assert job.status == "succeeded"
        assert job.result == expected
