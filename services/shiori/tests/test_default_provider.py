from __future__ import annotations

import pytest
from tsuyu_shiori.gateway import CachedProvider, default_provider


def test_ollama_is_explicit_and_mock_remains_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("SHIORI_PROVIDER", raising=False)
    assert "mock" in default_provider().cache_namespace
    monkeypatch.setenv("SHIORI_PROVIDER", "ollama")
    provider = default_provider()
    assert isinstance(provider, CachedProvider)
    assert "ollama" in provider.cache_namespace
    monkeypatch.setenv("SHIORI_PROVIDER", "unknown")
    with pytest.raises(ValueError, match="ollama"):
        default_provider()
