from __future__ import annotations

import json
from pathlib import Path

import pytest
from tsuyu_shiori.eval import evaluate, readability, write_report
from tsuyu_shiori.gateway import MockProvider, Response


@pytest.mark.eval
@pytest.mark.parametrize("seed", [37, 91])
async def test_generated_week_passes_gate(seed: int, tmp_path: Path) -> None:
    report = await evaluate(seed=seed)
    assert report["passed"]
    assert report["accuracy"] == 1
    assert report["verification_rate"] == 1
    assert report["cost_per_answer_usd"] == 0
    assert {r["expected"] for r in report["results"] if r["category"] == "count"} == {0, 1, 2, 3}
    assert report["topic_accuracy"] == report["readability_rate"] == 1
    assert report["max_ids_per_answer"] <= 6 and report["max_answer_length"] <= 160
    write_report(report, tmp_path)
    assert json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))["passed"]
    assert (tmp_path / "report.md").exists()


@pytest.mark.eval
async def test_gate_rejects_provider_that_only_invents_evidence() -> None:
    class Invented(MockProvider):
        async def complete(self, messages: list, tools: list, model: str) -> Response:
            return Response("該当する記録は3回です #fake-id。")

    report = await evaluate(Invented())
    assert not report["passed"]
    assert report["accuracy"] == report["verification_rate"] == 0


@pytest.mark.parametrize(
    "text",
    [
        "",
        "引用なし。",
        "観察 #0001。" * 7,
        "長" * 160 + " #0001。",
        "観察 #0001 #0002 #0003 #0004 #0005。",
    ],
)
def test_readability_rejects_unreadable_answers(text: str) -> None:
    assert not readability(text)["passed"]


@pytest.mark.eval
async def test_readability_gate_rejects_correct_but_verbose_provider() -> None:
    class Verbose(MockProvider):
        async def complete(self, messages: list, tools: list, model: str) -> Response:
            result = await super().complete(messages, tools, model)
            if result.text:
                return Response(result.text * 7)
            return result

    report = await evaluate(Verbose())
    assert report["accuracy"] == report["topic_accuracy"] == report["verification_rate"] == 1
    assert report["readability_rate"] == 0 and not report["passed"]
