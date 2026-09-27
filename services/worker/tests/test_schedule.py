from __future__ import annotations

from datetime import datetime, timedelta

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tsuyu_shiori.features import JST
from tsuyu_shiori.gateway import MockProvider
from tsuyu_worker.jobs import shiori_morning_memo
from tsuyu_worker.main import WorkerSettings, arq_shiori_answer, run_brain_job
from tsuyu_worker.schedule import active_users, nightly_memos
from tsuyulabo_api.db.models import ShioriMessage, User


async def test_jst_cron_activity_window_and_one_memo_per_day(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    now = datetime(2026, 9, 27, 3, 30, tzinfo=JST)
    async with sessions() as session, session.begin():
        await session.execute(update(User).values(created_at=now - timedelta(days=10)))
        session.add(
            User(
                id="inactive",
                display_name="inactive",
                friend_code="QRSTUVWX",
                created_at=now - timedelta(days=2),
            )
        )
        await session.flush()
        session.add(
            ShioriMessage(
                user_id="inactive",
                role="morning_memo",
                text="",
                evidence=[],
                cost={},
                created_at=now - timedelta(hours=1),
            )
        )
    assert await active_users(sessions, now) == ["other", "u"]
    result = await nightly_memos(sessions=sessions, provider=MockProvider(), now=now)
    assert result["generated"] == ["other", "u"]
    repeat = await nightly_memos(sessions=sessions, provider=MockProvider(), now=now)
    assert repeat["reused"] == ["other", "u"]
    direct = await shiori_morning_memo("u", sessions=sessions, provider=MockProvider(), now=now)
    assert direct["reused"]
    async with sessions() as session:
        assert (
            await session.scalar(
                select(func.count()).select_from(ShioriMessage).where(ShioriMessage.user_id == "u")
            )
            == 1
        )
    assert WorkerSettings.timezone.utcoffset(None) == timedelta(hours=9)
    schedule = WorkerSettings.cron_jobs[0]
    assert schedule.hour == 3 and schedule.minute == 30
    names = {getattr(f, "name", getattr(f, "__name__", "")) for f in WorkerSettings.functions}
    assert names == {
        "brain_run_experiment",
        "shiori_answer",
        "shiori_morning_memo",
        "run_brain_job",
    }


async def test_arq_wrappers_use_same_job_contract(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    from tsuyulabo_api.db.models import Job

    async with sessions() as session, session.begin():
        session.add_all(
            [
                Job(id="queue-1", user_id="u", kind="shiori_answer"),
                Job(id="queue-2", user_id="u", kind="shiori_answer"),
            ]
        )
    ctx = {"sessions": sessions, "provider": MockProvider()}
    result = await run_brain_job(ctx, "queue-1", "shiori_answer", {"question": "何回？"})
    direct = await arq_shiori_answer(ctx, "queue-2", {"question": "何回？"})
    assert result["answer"] == direct["answer"]
