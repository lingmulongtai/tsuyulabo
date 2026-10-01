"""Grade facts, independent of the deterministic provider's sentence templates."""

from __future__ import annotations

import re
import unicodedata


def normalized(text: str) -> str:
    return unicodedata.normalize("NFKC", text).replace("−", "-")


def count_answer(text: str) -> int | None:
    counts = {int(value) for value in re.findall(r"(?<![\d.+-])\+?(\d+)\s*回", normalized(text))}
    return counts.pop() if len(counts) == 1 else None


def has_facts(text: str, patterns: list[str]) -> bool:
    text = normalized(text)
    return all(re.search(pattern, text) is not None for pattern in patterns)


def number(value: str) -> str:
    suffix = r"0*" if "." in value else r"(?:\.0+)?"
    return rf"(?<![\d.+-])\+?{re.escape(value)}{suffix}(?![\d.])"


def citation(evidence_id: str) -> str:
    return re.escape(evidence_id) + r"(?![A-Za-z0-9_-])"


def action_count(action: str, count: int) -> str:
    value = number(str(count)) + r"\s*回"
    return rf"(?:{action})[^。\n\d]{{0,16}}{value}|{value}[^。\n\d]{{0,16}}(?:{action})"


TRIALS = action_count("試|実験|試行|テスト|trials|コピー", 20)
APPROACH = action_count("接近|近づ|向か|toward", 15)
AVOID = action_count("回避|離れ|避け|away", 14)
SUCCESS = action_count("大成功|great_success|成功", 1)
ABSENCE = r"(?:記録|データ)[^。\n]{0,24}(?:ありませ|ない|無い|なし|不足|未記録|見つかりませ)"
COLLECT = r"(?:記録|観察)[^。\n]{0,24}(?:残|集め|収集|記録して|追加|行い)"
