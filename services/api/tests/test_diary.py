from __future__ import annotations

from datetime import datetime

import pytest
from tsuyu_shiori.features import JST
from tsuyulabo_api.db.models import CareEvent, User, Week
from tsuyulabo_api.services.diary import generate, history


async def test_diary_is_dated_idempotent_and_owner_scoped(session):
    at = datetime(2026, 10, 12, 12, tzinfo=JST)
    session.add_all(
        [
            User(id="u", display_name="u", friend_code="AAAAAAAA"),
            User(id="other", display_name="o", friend_code="BBBBBBBB"),
        ]
    )
    await session.flush()
    session.add(Week(id="w", user_id="u", started_at=at))
    await session.flush()
    session.add(
        CareEvent(
            user_id="u",
            week_id="w",
            seq=1,
            kind="meal",
            research_day=1,
            created_at=at,
            payload={"great_success": True, "stage": "larva"},
        )
    )
    await session.flush()
    first = await generate(session, "u", "w", at.date())
    assert first["entry"]["snapshot"]["stage"] == "larva"
    assert first["entry"]["evidence"] == ["#0001"]
    assert (await generate(session, "u", "w", at.date()))["reused"]
    assert len(await history(session, "u", "w")) == 1
    with pytest.raises(ValueError):
        await history(session, "other", "w")
    assert (await generate(session, "u", "w", at.date().replace(day=11)))["skipped"]
