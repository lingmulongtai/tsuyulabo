"""Realistic player questions checked against facts rather than answer templates."""

from __future__ import annotations

import re
from collections import Counter

from tsuyu_shiori.eval_grading import APPROACH, AVOID, TRIALS, citation, number
from tsuyu_shiori.gateway.topics import CUES
from tsuyu_shiori.records import MemoryRecordStore, Record


def open_questions(store: MemoryRecordStore) -> list[tuple[str, list[str]]]:
    store.add(Record("#9006", "presentation", {"rank": "にじ"}, "eval-week"))
    counts = Counter(
        r.data["cue"]
        for r in store.records.values()
        if r.kind == "training" and r.week_id == "eval-week"
    )
    maximum = max(counts.values())
    labels = "|".join(re.escape(CUES[cue]) for cue, count in counts.items() if count == maximum)
    return [
        ("どうしてバナナに寄っていくの？", [number("0.47"), TRIALS, APPROACH]),
        ("りんご酢から離れるのはなんで？", [number("-0.4"), AVOID]),
        ("バナナの好みは変わった？", [number("0.47"), citation("#9001")]),
        ("最近よく眠れてる？", [number("7.7") + r"\s*時間", citation("#s-7")]),
        ("発表会のランクは？", ["にじ", citation("#9006")]),
        ("今週いちばん多かったしつけは？", [labels, number(str(maximum)) + r"\s*回"]),
        ("ごはんでうまくできたことは？", [r"大成功|great_success", citation("#9002")]),
        ("お部屋のそうじ、どうだった？", [number("80"), citation("#9003")]),
        ("温度あわせはうまくできた？", [number("90"), citation("#9004")]),
        ("羽化したツユの特徴を教えて", ["慎重", citation("#9005")]),
    ]
