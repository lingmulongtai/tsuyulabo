from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from tsuyu_shiori.features import JST
from tsuyulabo_api.db.models import LarvaState, User, Week
from tsuyulabo_api.domain.vial import initial
from tsuyulabo_api.services.quiet_hint import current, dismiss


async def test_hint_cooldown_dismissal_resolution_and_ownership(session):
    now = datetime(2026, 10, 13, 12, tzinfo=JST)
    session.add(User(id="u", display_name="u", friend_code="AAAAAAAA"))
    await session.flush()
    session.add(Week(id="w", user_id="u", started_at=now - timedelta(days=2)))
    await session.flush()
    state = LarvaState(week_id="w", last_computed_at=now, vial=initial(now) | {"temperature": 32})
    session.add(state)
    await session.flush()
    hint = await current(session, "u", "w", now)
    assert "暑く" in hint["text"] and "下げ" in hint["text"]
    assert (await current(session, "u", "w", now))["id"] == hint["id"]
    with pytest.raises(ValueError):
        await dismiss(session, "other", hint["id"], now)
    await dismiss(session, "u", hint["id"], now)
    assert await current(session, "u", "w", now + timedelta(minutes=1)) is None
    state.vial = initial(now)
    assert await current(session, "u", "w", now + timedelta(minutes=2)) is None
    state.vial = initial(now) | {"temperature": 32}
    later = await current(session, "u", "w", now + timedelta(hours=7))
    assert later["id"] != hint["id"]
