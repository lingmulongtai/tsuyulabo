"""Topic selection and short observations grounded exclusively in returned records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from tsuyu_shiori.verify import ID_PATTERN

RecordData = dict[str, Any]
CUES = {
    "banana": "バナナ",
    "apple_vinegar": "りんご酢",
    "yeast": "酵母",
    "grape": "ぶどう",
    "blue_light": "青い光",
}
KINDS = {
    "training": "しつけ",
    "meal": "ごはん",
    "cleaning": "そうじ",
    "temperature": "温度あわせ",
    "pupation_site": "場所えらび",
    "sleep": "睡眠",
    "eclosion": "羽化・特性",
    "presentation": "研究発表会",
}
WORDS = {
    "presentation": ("発表会", "ランク"),
    "sleep": ("睡眠", "眠", "寝", "ねむ", "おやすみ"),
    "eclosion": ("羽化", "特性", "素質", "成虫", "性別"),
    "meal": ("ごはん", "食事", "大成功", "えさ", "餌"),
    "cleaning": ("そうじ", "掃除", "清潔"),
    "temperature": ("温度", "気温"),
    "pupation_site": ("場所えらび", "さなぎ"),
    "training": ("しつけ", "学習", "覚え", "覚える", "脳", "好み", "連合"),
}


def cue_in(question: str) -> str | None:
    return next((cue for cue, label in CUES.items() if cue in question or label in question), None)


def topic_in(question: str) -> str | None:
    return next(
        (
            kind
            for kind, words in WORDS.items()
            if kind in question or any(w in question for w in words)
        ),
        "training" if cue_in(question) else None,
    )


def newest(records: list[RecordData]) -> list[RecordData]:
    def key(record: RecordData) -> tuple[float, int]:
        at = record.get("occurred_at")
        timestamp = datetime.fromisoformat(at).replace(tzinfo=UTC) if at else None
        if at and datetime.fromisoformat(at).tzinfo is not None:
            timestamp = datetime.fromisoformat(at)
        seq = record["id"].removeprefix("#")
        return (
            timestamp.timestamp() if timestamp else float("-inf"),
            int(seq) if seq.isdigit() else 0,
        )

    # Reverse input order is the fallback for undated, non-sequential IDs.
    return sorted(reversed(records), key=key, reverse=True)


def citations(records: list[RecordData], limit: int = 3) -> str:
    return " ".join(list(dict.fromkeys(r["id"] for r in newest(records)))[:limit])


def compact(sentences: list[str]) -> str:
    """Keep complete cited sentences; never truncate a claim or an evidence ID."""
    answer = ""
    for sentence in sentences:
        ids = ID_PATTERN.findall(sentence)
        if not ids or len(ids) > 4:
            continue
        if len(ID_PATTERN.findall(answer)) + len(ids) <= 6 and len(answer + sentence) <= 160:
            answer += sentence
        if answer.count("。") == 3:
            break
    return answer


def observations(
    question: str, care: list[RecordData], sleeps: list[RecordData], records: list[RecordData]
) -> list[str]:
    topic, cue = topic_in(question), cue_in(question)
    selected = newest(sleeps if topic == "sleep" else care)
    if topic and topic != "sleep":
        selected = [r for r in selected if r["kind"] == topic]
    if cue:
        selected = [r for r in selected if r["data"].get("cue") == cue]
    sentences: list[str] = []
    label = KINDS.get(topic, "お世話")
    if topic == "training":
        # For a broad learning question, follow the most recently trained cue.
        cue = cue or next(
            (r["data"].get("cue") for r in selected if r["data"].get("cue") in CUES), None
        )
        if cue:
            selected = [r for r in selected if r["data"].get("cue") == cue]
        label = f"{CUES[cue]}のしつけ" if cue else label
    if selected:
        latest, refs = selected[0], citations(selected, 2)
        data = latest["data"]
        if topic == "training":
            rewards = [r for r in selected if r["data"].get("valence") == "reward"]
            punishments = [r for r in selected if r["data"].get("valence") == "punish"]
            if len(rewards) + len(punishments) == len(selected):
                refs = " ".join(r["id"] for r in (rewards[:1] + punishments[:1]))
                sentences.append(
                    f"{label}は、ごほうび{len(rewards)}回、"
                    f"罰{len(punishments)}回の記録です {refs}。"
                )
            else:
                sentences.append(f"{label}が{len(selected)}回記録されています {refs}。")
        elif topic == "sleep":
            hours = data.get("hours")
            detail = f"{hours:.1f}時間" if hours is not None else "開始のみで、長さは未確定"
            sentences.append(f"直近の睡眠は{detail}です {latest['id']}。")
        elif topic == "meal" and (
            "大成功" in question or any(r["data"].get("great_success") is True for r in selected)
        ):
            successes = [r for r in selected if r["data"].get("great_success") is True]
            sentences.append(
                f"ごはんの大成功は{len(successes)}回記録されています "
                f"{citations(successes or selected, 2)}。"
            )
        elif topic == "eclosion":
            traits = data.get("traits")
            detail = f"特性は「{'・'.join(traits)}」" if traits else "羽化"
            sentences.append(f"{detail}が記録されています {latest['id']}。")
        elif topic == "presentation" and "rank" in data:
            sentences.append(f"研究発表会のランクは{data['rank']}です {latest['id']}。")
        else:
            detail = f"、直近のスコアは{data['score']}" if data.get("score") is not None else ""
            sentences.append(f"{label}は{len(selected)}回{detail}です {refs}。")
    if topic == "training" and cue:
        measured = newest(
            [
                r
                for r in records
                if r["kind"] in {"training", "association"}
                and r["data"].get("cue") == cue
                and r["data"].get("value") is not None
            ]
        )
        if measured:
            latest = measured[0]
            sentences.append(
                f"{CUES[cue]}の直近の好みの値は{latest['data']['value']:+.2f}です {latest['id']}。"
            )
        experiments = [
            r for r in records if r["kind"] == "experiment" and r["data"].get("cue") == cue
        ]
        if experiments:
            experiment = experiments[-1]
            data = experiment["data"]
            sentences.append(
                f"コピーで{data['trials']}回試すと、接近{data['toward']}回、"
                f"回避{data['away']}回でした {experiment['id']}。"
            )
    if not sentences:
        inspected = newest(care + sleeps)
        if not inspected:
            return []  # There is no existing ID to cite; the UI supplies an empty-state message.
        refs = citations(inspected, 1)
        sentences.append(f"確認した今週の記録には、{label}の該当記録がありません {refs}。")
        sentences.append(f"次は{label}の記録を残してから、一緒に確かめましょう {refs}。")
    elif len(sentences) == 1:
        refs = ID_PATTERN.findall(sentences[0])[0]
        suggestion = {
            "training": "しつけ前後の好みの値も比べて、変化を確かめましょう",
            "sleep": "次の睡眠と長さを比べて観察しましょう",
            "meal": "次のごはんの結果と比べて観察しましょう",
            "eclosion": "この記録だけでは特性の原因は断定できません",
        }.get(topic, "次のお世話の結果と比べて観察しましょう")
        sentences.append(f"{suggestion} {refs}。")
    return sentences
