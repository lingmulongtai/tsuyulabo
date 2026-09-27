from __future__ import annotations

import pytest
from tsuyu_shiori.records import MemoryRecordStore, Record
from tsuyu_shiori.verify import extract_ids, split_sentences, verify


async def test_drops_missing_fake_and_unseen_ids() -> None:
    store = MemoryRecordStore([Record("#0412", "meal"), Record("#c-19", "experiment")])
    result = await verify(
        "記録です #0412。偽です #9999。根拠なし。実験 #c-19。",
        store,
        allowed_ids={"#0412", "#9999"},
    )
    assert result.text == "記録です #0412。"
    assert result.report.kept == 1
    assert result.report.dropped == 3
    assert result.report.rate == 0.25
    assert extract_ids("#0412 #c-19 #0412") == ["#0412", "#c-19"]


@pytest.mark.parametrize("expression", ["悲しんで", "うれしがって", "怒って", "嬉しい"])
async def test_drops_emotion_without_inventing_behavior(expression: str) -> None:
    result = await verify(
        f"{expression}います #0412。", MemoryRecordStore([Record("#0412", "meal")])
    )
    assert not result.text
    assert result.report.reasons == ("banned_expression",)


async def test_mixed_valid_and_invalid_id_is_dropped() -> None:
    result = await verify("結果 #0412 #c-999。", MemoryRecordStore([Record("#0412", "meal")]))
    assert result.report.kept == 0
    assert split_sentences("値は0.5 #0412。次！\n最後？") == ["値は0.5 #0412。", "次！", "最後？"]
    assert (await verify("", MemoryRecordStore())).report.rate == 0
