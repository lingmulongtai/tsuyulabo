from __future__ import annotations

from unittest.mock import AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tsuyulabo_api.db.users import User
from tsuyulabo_api.services.jobs import ArqJobQueue, BrainClient, InlineJobQueue


async def test_inline_and_failed_jobs(sessions: async_sessionmaker[AsyncSession]) -> None:
    async with sessions() as session, session.begin():
        user = User(display_name="test", friend_code="ABCDEFGH")
        session.add(user)
        await session.flush()
        user_id = user.id

    queue = InlineJobQueue(sessions, {"double": lambda params: {"value": params["value"] * 2}})
    client = BrainClient(sessions, queue)
    job = await client.submit(user_id, "double", {"value": 4})
    assert job.status == "succeeded" and job.result == {"value": 8}
    assert job.finished_at is not None
    failed = await client.submit(user_id, "missing_handler", {})
    assert failed.status == "failed" and failed.error["code"] == "job_failed"
    queue = AsyncMock()
    queue.enqueue.side_effect = ConnectionError("private redis details")
    failed = await BrainClient(sessions, queue).submit(user_id, "double", {})
    assert failed.status == "failed" and failed.error["code"] == "enqueue_failed"
    assert "private" not in str(failed.error)


async def test_arq_enqueue_contract() -> None:
    queue = ArqJobQueue("redis://localhost:6379/0")
    queue.pool = AsyncMock()
    await queue.enqueue("job-id", "learn", {"fly_id": "fly"})
    queue.pool.enqueue_job.assert_awaited_once_with(
        "run_brain_job", "job-id", "learn", {"fly_id": "fly"}, _job_id="job-id"
    )
    await queue.close()
    queue.pool.aclose.assert_awaited_once()
