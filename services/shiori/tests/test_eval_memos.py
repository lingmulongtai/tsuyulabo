from __future__ import annotations

import sys

import pytest
from tsuyu_shiori.eval_memos import evaluate_memos, main
from tsuyu_shiori.gateway import MockProvider, Response


async def test_three_memos_use_journal_model_and_night_windows() -> None:
    class JournalOnly(MockProvider):
        async def complete(self, messages: list, tools: list, model: str) -> Response:
            assert model == "mock-journal"
            return await super().complete(messages, tools, model)

    report = await evaluate_memos(JournalOnly())
    assert len(report["results"]) == 3
    for result, hours in zip(report["results"], (7.2, 7.4, 7.7), strict=True):
        assert f"{hours}時間" in result["provider_text"]
        assert result["provider_verification"]["rate"] == 1
        assert not result["fallback_used"] and result["readability"]["passed"]


@pytest.mark.parametrize("enabled,ci", [("0", ""), ("1", "true")])
def test_live_memos_require_opt_in_and_reject_ci(
    monkeypatch: pytest.MonkeyPatch, enabled: str, ci: str
) -> None:
    monkeypatch.setenv("SHIORI_LIVE_EVAL", enabled)
    monkeypatch.setenv("CI", ci)
    monkeypatch.setattr(sys, "argv", ["eval_memos", "--provider", "ollama"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2
