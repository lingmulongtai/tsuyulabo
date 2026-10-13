"""Visible habitat consequences; never changes puzzle scores or biological rewards."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from . import constants as c
from .puzzles.temperature import temperature_at


def initial(now: datetime) -> dict[str, Any]:
    return {
        "food": {"color": "#bda45c", "moisture": 0.7, "yeast": 0.2, "nutrition": 0.3},
        "humidity": 0.65,
        "temperature": 25.0,
        "mould": 0.0,
        "grime": 0.0,
        "updated_at": now.isoformat(),
        "fed_at": now.isoformat(),
        "pupation_position": [0.24, -0.05, 0.94],
    }


def settle(
    saved: dict[str, Any], now: datetime, hunger: float, cleanliness: float
) -> dict[str, Any]:
    value = initial(now) | saved
    hours = max(0, (now - datetime.fromisoformat(value["updated_at"])).total_seconds() / 3600)
    food = dict(value["food"])
    food["moisture"] = max(0, food["moisture"] - hours * 0.015)
    value["food"] = food
    value["mould"] = min(1, value["mould"] + hours * 0.006 * (1 - cleanliness / 100))
    value["grime"] = max(value["grime"], 1 - cleanliness / 100)
    value["pace"] = max(0.15, min(1, (hunger * 0.6 + cleanliness * 0.4) / 100))
    value["updated_at"] = now.isoformat()
    return value


def medium(params: dict[str, Any], body: dict[str, Any], score: int) -> dict[str, Any]:
    counts = dict.fromkeys(c.MATERIALS, 0)
    for move in body["moves"]:
        piece = params["pieces"][move["p"]]
        counts[piece["ingredient"]] += len(c.SHAPES[piece["shape"]])
    total = max(1, sum(counts.values()))
    colors = {
        "banana": (189, 164, 92),
        "apple": (196, 151, 111),
        "grape": (139, 109, 120),
        "yeast": (203, 183, 137),
        "agar": (219, 205, 163),
    }
    color = (
        "#"
        + "".join(
            f"{round(sum(colors[k][i] * n for k, n in counts.items()) / total):02x}"
            for i in range(3)
        )
        if sum(counts.values())
        else "#bda45c"
    )
    return {
        "color": color,
        "moisture": min(1, 0.55 + counts["agar"] / total * 0.4),
        "yeast": counts["yeast"] / total,
        "nutrition": min(1, score / 3000),
    }


def apply(
    saved: dict[str, Any],
    kind: str,
    params: dict[str, Any],
    body: dict[str, Any],
    result: dict[str, Any],
    now: datetime,
) -> dict[str, Any]:
    value = initial(now) | saved
    if kind == "meal":
        value.update(food=medium(params, body, result["score"]), fed_at=now.isoformat(), mould=0.0)
    elif kind == "cleaning":
        remaining = 1 - result["score"] / 100
        value.update(grime=value["grime"] * remaining, mould=value["mould"] * remaining)
    elif kind == "temperature":
        value["temperature"] = temperature_at(params, body["stop_ms"])
        value["humidity"] = body.get("humidity", value["humidity"])
    elif kind == "training":
        value["cue"] = params["cue"]
    elif kind == "pupation_site":
        option = next((o for o in params.get("options", []) if o["id"] == body["choice"]), {})
        value["pupation_position"] = option.get("position", [0.24, 1.15, 0.94])
    value["updated_at"] = now.isoformat()
    return value


def sites(params: dict[str, Any]) -> dict[str, Any]:
    positions = ([0.24, 0.55, 0.94], [-0.3, -1.0, 0.85], [0.2, 1.15, 0.94])
    return params | {
        "options": [
            option
            | {
                "position": positions[
                    next(
                        i
                        for i, pool in enumerate(c.SITE_TEXT_POOLS)
                        if (option["label"], option["detail"]) in pool
                    )
                ]
            }
            for option in params["options"]
        ]
    }
