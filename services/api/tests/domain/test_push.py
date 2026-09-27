from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError
from tsuyulabo_api.domain.clock import JST
from tsuyulabo_api.services.push_preferences import PushPreferences


@pytest.mark.parametrize("hour,quiet", [(23, True), (0, True), (4, True), (7, False), (22, False)])
def test_default_quiet_hours(hour: int, quiet: bool) -> None:
    now = datetime(2026, 9, 27, hour, tzinfo=JST)
    assert PushPreferences().is_quiet(now.astimezone(UTC)) is quiet


def test_daytime_and_disabled_quiet_hours() -> None:
    now = datetime(2026, 9, 27, 12, tzinfo=JST)
    assert PushPreferences(quiet_start="12:00", quiet_end="13:00").is_quiet(now)
    assert not PushPreferences(quiet_start="12:00", quiet_end="12:00").is_quiet(now)
    with pytest.raises(ValidationError):
        PushPreferences(quiet_start="24:00")
