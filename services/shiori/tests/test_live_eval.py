from __future__ import annotations

import os
import sys

import pytest
from tsuyu_shiori.eval import evaluate, main
from tsuyu_shiori.gateway import OllamaProvider


@pytest.mark.eval
@pytest.mark.skipif(
    os.getenv("SHIORI_LIVE_EVAL") != "1" or bool(os.getenv("CI")),
    reason="local live evaluation is opt-in and never runs in CI",
)
async def test_live_ollama_smoke() -> None:
    report = await evaluate(OllamaProvider(), limit=1)
    assert report["questions"] == 1
    assert report["input_tokens"] > 0


@pytest.mark.parametrize("enabled,ci", [("0", ""), ("1", "true")])
def test_cli_rejects_live_without_opt_in_or_inside_ci(
    monkeypatch: pytest.MonkeyPatch,
    enabled: str,
    ci: str,
) -> None:
    monkeypatch.setenv("SHIORI_LIVE_EVAL", enabled)
    monkeypatch.setenv("CI", ci)
    monkeypatch.setattr(sys, "argv", ["eval", "--provider", "ollama", "--limit", "1"])
    with pytest.raises(SystemExit) as exc:
        main()
    assert exc.value.code == 2
