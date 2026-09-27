"""Pure catalog, calendar and ranking rules for the cosmetic contest."""

from __future__ import annotations

from datetime import datetime, timedelta

from .clock import JST

ITEMS = {
    "plain_vial": ("vial", "透明ビン", "starter", None),
    "leaf_background": ("background", "若葉の背景", "starter", None),
    "rain_vial": ("vial", "雨粒ビン", "presentation", "silver"),
    "drop_ribbon": ("accessory", "しずくのリボン", "presentation", "silver"),
    "rainbow_background": ("background", "虹の背景", "presentation", "rainbow"),
    "banana_ornament": ("ornament", "バナナの飾り", "research", 2),
    "flower_ornament": ("ornament", "小さな花", "research", 6),
    "leaf_hat": ("accessory", "葉っぱの帽子", "research", 11),
}
SLOTS = {
    "vial": "vial",
    "background": "background",
    "left": "ornament",
    "right": "ornament",
    "accessory": "accessory",
}
THEMES = ("梅雨の研究所", "バナナ祭り", "緑の実験室", "虹の飼育室")
RANKS = {"normal": 0, "silver": 1, "gold": 2, "rainbow": 3}


def week_at(now: datetime) -> tuple[str, datetime, datetime, str]:
    local = now.astimezone(JST)
    year, number, _ = local.isocalendar()
    monday = (local - timedelta(days=local.weekday())).replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    return (
        f"{year}-W{number:02d}",
        monday + timedelta(days=5),
        monday + timedelta(days=7),
        THEMES[(number - 1) % len(THEMES)],
    )


def phase(now: datetime, entry_close: datetime, vote_close: datetime) -> str:
    if now < entry_close:
        return "entry"
    return "vote" if now < vote_close else "results"


def valid_layout(layout: dict[str, str | None]) -> bool:
    return set(layout) == set(SLOTS) and all(
        item is None or (item in ITEMS and ITEMS[item][0] == SLOTS[slot])
        for slot, item in layout.items()
    )


def rank_entries(entries: list[tuple[str, int, datetime]]) -> list[str]:
    return [
        entry_id for entry_id, _, _ in sorted(entries, key=lambda row: (-row[1], row[2], row[0]))
    ]
