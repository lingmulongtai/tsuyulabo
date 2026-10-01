"""Seeded fictional weeks; seed 37 is exactly the existing evaluation fixture."""

from __future__ import annotations

from datetime import timedelta
from random import Random

from tsuyu_shiori.eval import open_questions, synthesize, topic_questions
from tsuyu_shiori.gateway.topics import CUES
from tsuyu_shiori.records import MemoryLab, MemoryRecordStore, Record
from tsuyu_shiori.tools import ToolContext


def build_world(seed: int) -> ToolContext:
    store, _ = synthesize(seed)
    topic_questions(store)
    open_questions(store)
    states = {"banana": 0.47, "apple_vinegar": -0.4}
    if seed != 37:
        rng = Random(seed + 810)
        records = []
        for record in store.records.values():
            data = dict(record.data)
            if record.kind == "sleep":
                data.update(hours=round(rng.uniform(4, 10), 1), research_day=int(record.id[3:]))
            elif record.kind in {"cleaning", "temperature"}:
                data["score"] = rng.randrange(101)
            elif record.kind == "meal":
                data["great_success"] = rng.choice([True, False])
            elif record.kind == "presentation":
                data["rank"] = rng.choice(["normal", "silver", "gold", "rainbow"])
            elif record.kind == "eclosion":
                data["traits"] = [
                    rng.choice(["右曲がりぐせ", "左曲がりぐせ"]),
                    rng.choice(["光が大好き", "匂いにするどい", "度胸がある", "食いしんぼう"]),
                ]
            records.append(
                Record(
                    record.id, record.kind, data, record.week_id, record.fly_id, record.occurred_at
                )
            )
        store = MemoryRecordStore(records)
        start = next(r.occurred_at for r in records if r.occurred_at)
        for day in range(1, 8):
            for cue in ("yeast", "blue_light"):
                for valence in ("reward", "punish"):
                    for n in range(rng.randrange(5)):
                        store.add(
                            Record(
                                f"#x-{day}-{cue}-{valence}-{n}",
                                "training",
                                {"research_day": day, "cue": cue, "valence": valence},
                                "eval-week",
                                "eval-fly",
                                start + timedelta(days=day - 1),
                            )
                        )
        states = {cue: round(rng.uniform(-0.9, 0.9), 2) for cue in CUES}
        for cue, value in states.items():
            store.add(
                Record(
                    f"#a-{cue}",
                    "association",
                    {"cue": cue, "value": value},
                    "eval-week",
                    "eval-fly",
                )
            )
        if seed % 2:
            store.add(
                Record(
                    "#site", "pupation_site", {"score": rng.randrange(101)}, "eval-week", "eval-fly"
                )
            )
    return ToolContext(store, MemoryLab(store, {"eval-fly": states}), "eval-week", "eval-fly")
