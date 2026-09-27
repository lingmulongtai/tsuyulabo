"""Seeded, collection-aware names for newly eclosed adults."""

from __future__ import annotations

from random import Random

NAME_POOL = tuple(
    [
        "つゆまる",
        "しずく",
        "こはく",
        "ぴかり",
        "もなか",
        "すだち",
        "ルビー",
        "あめ",
        "みつ",
        "ほたる",
        "もも",
        "りんご",
        "いちご",
        "ぶどう",
        "ゆず",
        "かりん",
        "あんず",
        "こもも",
        "うめ",
        "びわ",
        "ぷりん",
        "きなこ",
        "あずき",
        "くるみ",
        "こむぎ",
        "まろん",
        "ぽぽ",
        "ころん",
        "ふわり",
        "まる",
        "ひかり",
        "きらり",
        "こぼし",
        "あかり",
        "ひなた",
        "こはる",
        "あさひ",
        "にじ",
        "そら",
        "ほし",
        "わかば",
        "ふたば",
        "よつば",
        "つぼみ",
        "こけ",
        "しろ",
        "ゆき",
        "しらたま",
        "くろまめ",
        "ごま",
        "すみ",
        "たんぽぽ",
        "こがね",
        "れもん",
        "くるり",
        "まき",
        "ちい",
        "こつぶ",
        "るぺ",
        "ぴぺ",
    ]
)

THEMED_NAMES = {
    "white": ("ゆき", "しろ", "しらたま"),
    "ebony": ("くろまめ", "ごま", "すみ"),
    "yellow": ("たんぽぽ", "こがね", "れもん"),
    "curly": ("くるり", "まき", "ころん"),
    "vestigial": ("ちい", "こつぶ", "ふわり"),
}


def pick_name(rng: Random, taken: set[str], *, strain: str | None = None) -> str:
    """Prefer unused themed names, then the pool, then an unused numbered name."""
    preferred = [name for name in THEMED_NAMES.get(strain, ()) if name not in taken]
    available = preferred or [name for name in NAME_POOL if name not in taken]
    if available:
        return rng.choice(available)
    base = rng.choice(THEMED_NAMES.get(strain, NAME_POOL))
    number = 2
    while f"{base}{number}" in taken:
        number += 1
    return f"{base}{number}"
