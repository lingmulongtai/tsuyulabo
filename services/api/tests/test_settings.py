from __future__ import annotations

import pytest
from pydantic import ValidationError
from tsuyulabo_api.settings import Settings


def test_defaults_and_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    defaults = Settings(_env_file=None)
    assert defaults.database_url == "sqlite+aiosqlite:///./tsuyulabo.db"
    assert defaults.brain_mode == "inline"
    assert not defaults.dev_tools
    monkeypatch.setenv("TSUYU_DEV_TOOLS", "1")
    monkeypatch.setenv("JWT_SECRET", "test-secret")
    monkeypatch.setenv("CORS_ORIGINS", '["https://example.test"]')
    settings = Settings(_env_file=None)
    assert settings.dev_tools
    assert settings.jwt_secret.get_secret_value() == "test-secret"
    assert settings.cors_origins == ["https://example.test"]
    assert "test-secret" not in repr(settings)


def test_invalid_mode() -> None:
    with pytest.raises(ValidationError):
        Settings(brain_mode="invalid", _env_file=None)


@pytest.mark.parametrize(
    "secret", ["", "short", "x" * 31, "local-development-only-change-before-deploying"]
)
def test_production_rejects_unsafe_secret(monkeypatch: pytest.MonkeyPatch, secret: str) -> None:
    monkeypatch.setenv("TSUYU_ENV", "production")
    monkeypatch.setenv("JWT_SECRET", secret)
    with pytest.raises(ValidationError, match="JWT_SECRET"):
        Settings(_env_file=None)


def test_production_accepts_explicit_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TSUYU_ENV", "production")
    settings = Settings(jwt_secret="x" * 32, _env_file=None)
    assert settings.environment == "production"


def test_unknown_environment_fails_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TSUYU_ENV", "prodution")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
