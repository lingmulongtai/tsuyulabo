"""Quiet hints require measured state; absence is never a measurement."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from math import isfinite
from typing import Any


@dataclass(frozen=True)
class Trouble:
    kind: str
    observation: str
    help: str


def detect_trouble(state: dict[str, Any], now: datetime) -> Trouble | None:
    def measured(value: Any) -> bool:
        return isinstance(value, (float, int)) and not isinstance(value, bool) and isfinite(value)

    temperature = state.get("temperature")
    if measured(temperature) and temperature > 29:
        return Trouble("hot", "びんが暑くなっています", "温度を少し下げてみましょう")
    if measured(temperature) and temperature < 18:
        return Trouble("cold", "びんが冷えています", "温度を少し上げてみましょう")
    mould = state.get("mould")
    if measured(mould) and mould > 0.2:
        return Trouble("mould", "餌のまわりにカビが出ています", "そうじで取り除きましょう")
    moisture = state.get("food", {}).get("moisture")
    if measured(moisture) and moisture < 0.3:
        return Trouble("dry", "餌が乾いてきています", "しっとりしたごはんを入れましょう")
    fed_at = state.get("fed_at")
    if isinstance(fed_at, str):
        try:
            fed = datetime.fromisoformat(fed_at)
            if fed.tzinfo is not None and now - fed > timedelta(hours=12):
                return Trouble(
                    "meal", "前のごはんから時間が空いています", "次のごはんを用意しましょう"
                )
        except ValueError:
            pass
    if state.get("behaviour") in {"escape", "flee"}:
        return Trouble("stress", "逃げる動きが続いています", "温度や餌の様子を確かめましょう")
    return None
