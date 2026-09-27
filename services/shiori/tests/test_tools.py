from __future__ import annotations

import pytest
from tsuyu_shiori.records import MemoryLab, MemoryRecordStore, Record
from tsuyu_shiori.tools import SCHEMAS, ToolContext, execute


async def test_tools_validate_scope_and_persist_evidence() -> None:
    store = MemoryRecordStore(
        [Record("#0001", "training", {"cue": "banana", "value": 0.5}, "w", "f")]
    )
    context = ToolContext(store, MemoryLab(store, {"f": {"banana": 0.5}}), "w", "f")
    assert len(SCHEMAS) == 4
    care = await execute(context, "get_care_events", {"week_id": "w"})
    assert care["records"][0]["id"] == "#0001"
    result = await execute(context, "run_odor_choice", {"fly_id": "f", "cue": "banana"})
    assert await store.exists(result["records"][0]["id"])
    assert (await execute(context, "search_papers", {"query": "MN9"}))["papers"]
    for name, args in [
        ("get_care_events", {"week_id": "other"}),
        ("get_association", {"fly_id": "other", "cue": "banana"}),
        ("run_odor_choice", {"fly_id": "f", "cue": "banana", "trials": 1001}),
        ("run_odor_choice", {"fly_id": "f", "cue": "banana", "trials": True}),
        ("search_papers", {"query": "x", "extra": True}),
        ("unknown", {}),
    ]:
        with pytest.raises(ValueError):
            await execute(context, name, args)
