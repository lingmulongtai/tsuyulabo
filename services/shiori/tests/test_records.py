from __future__ import annotations

from tsuyu_shiori.records import MemoryLab, MemoryRecordStore, Record


async def test_records_are_filtered_and_copied() -> None:
    store = MemoryRecordStore(
        [
            Record("#0001", "training", {"cue": "banana", "value": 0.5}, "w", "f"),
            Record("#s-1", "sleep", {}, "w"),
            Record("#0002", "meal", {}, "other"),
        ]
    )
    records = await store.care_events("w", ["training"])
    records[0].data["value"] = 99
    assert (await store.association("f", "banana")).data["value"] == 0.5
    assert len(await store.sleep_sessions("w")) == 1
    assert not await store.exists("#9999")
    lab = MemoryLab(store, {"f": {"banana": 0.5}})
    result = await lab.run_odor_choice("f", "banana")
    assert result.data["toward"] == 15
    assert await store.experiment(result.id) == result
    assert lab.states == {"f": {"banana": 0.5}}
