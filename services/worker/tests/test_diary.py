from __future__ import annotations

from datetime import datetime

from tsuyu_shiori.features import JST
from tsuyu_worker.diary import nightly_diaries


async def test_batch_generates_previous_jst_day_and_reuses(sessions):
    now = datetime(2026, 9, 27, 3, 30, tzinfo=JST)
    first = await nightly_diaries(sessions=sessions, now=now)
    assert first["generated"] == ["other-w", "w"]
    assert not first["failed"]
    second = await nightly_diaries(sessions=sessions, now=now)
    assert second["reused"] == first["generated"]
    assert not second["generated"]
