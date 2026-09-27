from __future__ import annotations

from datetime import datetime

from tsuyu_shiori.features import JST, coach_tip, morning_memo, presentation_host
from tsuyu_shiori.gateway import MockProvider
from tsuyu_shiori.records import MemoryLab, MemoryRecordStore, Record
from tsuyu_shiori.verify import split_sentences


async def test_features_use_time_window_rank_and_sentence_limits() -> None:
    store = MemoryRecordStore(
        [
            Record("#0001", "meal", {}, "w", occurred_at=datetime(2026, 9, 25, 10, tzinfo=JST)),
            Record("#0002", "meal", {}, "w", occurred_at=datetime(2026, 9, 26, 10, tzinfo=JST)),
            Record(
                "#s-1",
                "sleep",
                {"hours": 7.5},
                "w",
                occurred_at=datetime(2026, 9, 26, 22, tzinfo=JST),
            ),
            Record("#0003", "presentation", {"rank": "にじ"}, "w"),
        ]
    )
    kwargs = {
        "store": store,
        "lab": MemoryLab(store, {"f": {}}),
        "week_id": "w",
        "fly_id": "f",
        "provider": MockProvider(),
    }
    memo = await morning_memo(**kwargs, now=datetime(2026, 9, 27, 8, tzinfo=JST))
    assert len(split_sentences(memo.text)) == 3
    assert memo.evidence_ids == ["#0002", "#s-1"]
    assert "7.5時間" in memo.text
    assert len(split_sentences((await coach_tip(**kwargs)).text)) == 1
    presentation = await presentation_host(**kwargs)
    assert "にじ" in presentation.text
    assert "#0003" in presentation.evidence_ids
    assert presentation.verification.rate == 1
