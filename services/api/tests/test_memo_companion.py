from __future__ import annotations

from datetime import UTC, datetime

from tsuyulabo_api.db.models import ShioriMessage, User
from tsuyulabo_api.services.memo import today


async def test_worker_morning_memo_is_readable(session):
    now = datetime(2026, 10, 13, tzinfo=UTC)
    session.add(User(id="u", display_name="u", friend_code="AAAAAAAA"))
    await session.flush()
    session.add(
        ShioriMessage(
            user_id="u", role="morning_memo", text="朝のメモ", evidence=[], cost={}, created_at=now
        )
    )
    await session.flush()
    assert (await today(session, "u", now))["text"] == "朝のメモ"
