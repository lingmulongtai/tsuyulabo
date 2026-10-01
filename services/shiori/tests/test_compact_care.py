from __future__ import annotations

from tsuyu_shiori.records import Record
from tsuyu_shiori.tools.compact import compact_result


def test_combined_cap_and_compact_fields() -> None:
    care = [Record(f"#{i:04}", "meal", {"score": i, "payload": "x" * 10000}) for i in range(30)]
    result = compact_result(care, [Record("#9999", "sleep", {"hours": 8})])
    assert result["total"] == 31 and result["truncated"]
    assert len(result["records"]) + len(result["sleep_sessions"]) == 20
    assert result["sleep_sessions"][0]["data"] == {"hours": 8}
    assert result["records"][0] == {
        "id": "#0029",
        "kind": "meal",
        "research_day": None,
        "data": {"score": 29},
    }
    assert "payload" not in str(result)


def test_empty_and_exact_cap_are_not_truncated() -> None:
    assert compact_result([], []) == {
        "records": [],
        "sleep_sessions": [],
        "total": 0,
        "truncated": False,
    }
    assert not compact_result([Record(f"#{i}", "meal") for i in range(20)], [])["truncated"]
