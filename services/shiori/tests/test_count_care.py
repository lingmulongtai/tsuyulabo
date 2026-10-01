from __future__ import annotations

import pytest
from tsuyu_shiori.agent import run_agent
from tsuyu_shiori.gateway import MockProvider
from tsuyu_shiori.records import MemoryLab, MemoryRecordStore, Record
from tsuyu_shiori.tools import ToolContext, execute


async def test_exact_count_exceeds_cap_and_echoes_filters() -> None:
    class HostStore(MemoryRecordStore):
        async def care_events(self, week_id: str, kinds: list[str] | None = None) -> list[Record]:
            assert kinds is None  # Filtering must happen after the host's read.
            return await super().care_events(week_id)

    store = HostStore(
        [
            Record(
                f"#{i:04}",
                "training",
                {"research_day": 3, "cue": "banana", "valence": "reward"},
                "w",
            )
            for i in range(35)
        ]
        + [Record("#s-1", "sleep", {"hours": 8}, "w")]
    )
    context = ToolContext(store, MemoryLab(store, {}), "w", "f")
    args = {"week_id": "w", "research_day": 3, "cue": "banana", "valence": "reward"}
    count = await execute(context, "count_care_events", args)
    assert count == {
        "count": 35,
        "ids": ["#0034", "#0033", "#0032", "#0031"],
        "filters": {**args, "kinds": None},
    }
    care = await execute(context, "get_care_events", args)
    assert len(care["records"]) == 20 and care["total"] == 35 and care["truncated"]
    sleep = await execute(context, "get_care_events", {"week_id": "w", "kinds": ["sleep"]})
    assert sleep["sleep_sessions"][0]["data"]["hours"] == 8
    assert (await execute(context, "count_care_events", {"week_id": "w"}))["count"] == 36
    assert (await execute(context, "count_care_events", {"week_id": "w", "kinds": ["sleep"]}))[
        "count"
    ] == 1
    answer = await run_agent("3日目にバナナで報酬を何回覚えた？", context, provider=MockProvider())
    assert "35回" in answer.text and answer.steps == 2 and not answer.fallback_used
    assert (await execute(context, "count_care_events", {"week_id": "w", "kinds": []}))[
        "count"
    ] == 0
    with pytest.raises(ValueError):
        await execute(context, "count_care_events", {"week_id": "other"})


async def test_zero_count_cites_inspected_records_or_returns_no_ids() -> None:
    store = MemoryRecordStore([Record("#0001", "meal", {}, "w")])
    context = ToolContext(store, MemoryLab(store, {}), "w", "f")
    args = {"week_id": "w", "cue": "grape"}
    assert (await execute(context, "count_care_events", args))["ids"] == ["#0001"]
    store.records.clear()
    assert (await execute(context, "count_care_events", args))["ids"] == []
