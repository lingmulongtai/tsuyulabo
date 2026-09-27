from __future__ import annotations

from collections.abc import AsyncIterator
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tsuyu_shiori.features import JST
from tsuyulabo_api.db.models import Adult, Base, CareEvent, SleepSession, User, Week
from tsuyulabo_api.db.session import create_engine, session_factory


@pytest.fixture
async def sessions(tmp_path: Path) -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    engine = create_engine(f"sqlite+aiosqlite:///{tmp_path / 'worker.db'}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    factory = session_factory(engine)
    at = datetime(2026, 9, 26, 9, tzinfo=JST)
    async with factory() as session, session.begin():
        session.add_all(
            [
                User(id="u", display_name="test", friend_code="ABCDEFGH"),
                User(id="other", display_name="other", friend_code="IJKLMNOP"),
            ]
        )
        await session.flush()
        session.add_all(
            [
                Week(id="w", user_id="u", started_at=at - timedelta(days=1)),
                Week(id="other-w", user_id="other", started_at=at),
            ]
        )
        await session.flush()
        session.add(
            Adult(
                id="f",
                user_id="u",
                week_id="w",
                name="ツユ",
                sex="f",
                strain="wild",
                stars=1,
                brain_params={"associations": {"banana": 0.4}},
                learned_weights=b"state",
            )
        )
        session.add_all(
            [
                CareEvent(
                    user_id="u",
                    week_id="w",
                    seq=1,
                    kind="training",
                    research_day=2,
                    payload={
                        "cue": "banana",
                        "valence": "reward",
                        "association_value": 0.5,
                        "learning_strength": 0.1,
                    },
                    created_at=at,
                ),
                CareEvent(
                    user_id="other",
                    week_id="other-w",
                    seq=2,
                    kind="meal",
                    research_day=1,
                    created_at=at,
                ),
                SleepSession(
                    id="sleep-1",
                    user_id="u",
                    started_at=at + timedelta(hours=13),
                    ended_at=at + timedelta(hours=21),
                ),
            ]
        )
    yield factory
    await engine.dispose()
