from __future__ import annotations

from tsuyu_shiori.eval_companion import evaluate_companion, grade


async def test_mock_companion_gate_grades_facts_and_each_intent():
    report = await evaluate_companion()
    assert report["passed"] and report["accuracy"] == 1
    assert report["questions"] == 13
    assert {r["intent"] for r in report["results"]} == {"diary", "hint", "behaviour-why", "morning"}


def test_existing_id_does_not_excuse_invented_unmeasured_value():
    payload = {
        "feature": "behaviour-why",
        "observation": {"label": "歩く"},
        "context_text": "酵母の好みはまだ未記録です #0001。",
    }
    assert grade("脳の出力は歩く動きです #0001。酵母はまだ未記録です #0001。", payload, ["#0001"])
    assert not grade(
        "脳の出力は歩く動きです #0001。まだ未記録ですが好みは+0.47です #0001。", payload, ["#0001"]
    )
    assert not grade(
        "脳の出力は歩く動きです #0001。まだ未記録ですが好みは-1です #0001。", payload, ["#0001"]
    )
