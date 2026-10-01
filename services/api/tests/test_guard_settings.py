from __future__ import annotations

import pytest
from pydantic import ValidationError
from tsuyulabo_api.settings import Settings


def test_guard_defaults_and_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = Settings(_env_file=None)
    assert settings.rate_guest_hour == 5
    assert settings.rate_guest_day_global == 200
    assert settings.job_max_per_user == 2
    assert settings.job_max_total == 20
    assert settings.trusted_proxy_hops == 1
    monkeypatch.setenv("RATE_BRAIN_MINUTE", "7")
    monkeypatch.setenv("TRUSTED_PROXY_HOPS", "0")
    assert Settings(_env_file=None).rate_brain_minute == 7
    assert Settings(_env_file=None).trusted_proxy_hops == 0


@pytest.mark.parametrize("field", ["rate_guest_hour", "job_max_total", "job_busy_retry_after"])
def test_guard_limits_must_be_positive(field: str) -> None:
    with pytest.raises(ValidationError):
        Settings(**{field: 0}, _env_file=None)
