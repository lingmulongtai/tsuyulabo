from __future__ import annotations

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tsuyu_worker.adapters import SQLLab, SQLRecordStore, conversation_scope
from tsuyu_worker.brain_adapter import FakeBrainEngine
from tsuyulabo_api.db.models import Adult, Experiment


async def test_user_scoping_and_copy_experiments(
    sessions: async_sessionmaker[AsyncSession],
) -> None:
    async with sessions() as session, session.begin():
        store = SQLRecordStore(session, "u")
        assert len(await store.care_events("w")) == 1
        assert (await store.sleep_sessions("w"))[0].data["hours"] == 8
        assert (await store.association("f", "banana")).data["value"] == 0.5
        assert await store.exists("#0001")
        assert not await store.exists("#0002")
        assert not await store.exists("#1")
        assert await store.exists("#s-sleep-1")
        assert not await SQLRecordStore(session, "other").exists("#s-sleep-1")
        for call in (store.care_events("other-w"), store.association("other-w", "banana")):
            with pytest.raises(ValueError):
                await call
        lab = SQLLab(session, "u", FakeBrainEngine())
        first = await lab.run_odor_choice("f", "banana")
        second = await lab.run_odor_choice("f", "banana")
        assert first.id == "#c-1" and second.id == "#c-2"
        assert first.data["toward"] == 15
        assert await store.experiment(first.id) == first
        assert not await SQLRecordStore(session, "other").exists(first.id)
        assert len(list(await session.scalars(select(Experiment)))) == 2
        adult = await session.get(Adult, "f")
        assert adult.learned_weights == b"state"
        assert adult.brain_params == {"associations": {"banana": 0.4}}
        assert await conversation_scope(store, {"fly_id": "f"}) == ("w", "f")
        with pytest.raises(ValueError):
            await conversation_scope(store, {"week_id": "other-w", "fly_id": "f"})
