from __future__ import annotations

from datetime import datetime

from tsuyu_shiori.features import JST, morning_memo
from tsuyu_shiori.gateway import MockProvider
from tsuyu_shiori.records import MemoryLab, MemoryRecordStore, Record


async def test_morning_memo_does_not_observe_future_sleep() -> None:
    store = MemoryRecordStore(
        [
            Record("#0001", "meal", {}, "w", occurred_at=datetime(2026, 9, 22, 9, tzinfo=JST)),
            Record(
                "#s-1",
                "sleep",
                {"hours": 7.2},
                "w",
                occurred_at=datetime(2026, 9, 22, 22, tzinfo=JST),
            ),
            Record(
                "#s-2",
                "sleep",
                {"hours": 7.7},
                "w",
                occurred_at=datetime(2026, 9, 27, 22, tzinfo=JST),
            ),
        ]
    )
    answer = await morning_memo(
        store=store,
        lab=MemoryLab(store, {}),
        week_id="w",
        fly_id="f",
        now=datetime(2026, 9, 23, 8, tzinfo=JST),
        provider=MockProvider(),
    )
    assert "7.2時間" in answer.text and "7.7時間" not in answer.text
    assert "#s-2" not in answer.evidence_ids
