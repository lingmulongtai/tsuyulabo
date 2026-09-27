"""Quiet hours use real JST wall time, independently of dev time travel."""

from __future__ import annotations

from datetime import datetime

from .clock import local


def is_quiet(now: datetime, start: str = "23:00", end: str = "07:00") -> bool:
    """Evaluate validated HH:MM boundaries; equal boundaries disable quiet hours."""
    time = local(now).strftime("%H:%M")
    if start <= end:
        return start <= time < end
    return time >= start or time < end
