"""Conservative citation and wording checks; ID existence is not semantic entailment."""

from __future__ import annotations

import re
from dataclasses import dataclass

from tsuyu_shiori.records import RecordStore

ID_PATTERN = re.compile(r"#[A-Za-z0-9][A-Za-z0-9_-]*")
BANNED = ("悲しん", "悲しい", "うれし", "嬉し", "怒っ", "怒り", "寂し", "さびし")


def split_sentences(text: str) -> list[str]:
    # Decimal points and DOI punctuation are not Japanese sentence boundaries.
    return [part.strip() for part in re.findall(r"[^。！？!?\n]+[。！？!?]?", text) if part.strip()]


def extract_ids(text: str) -> list[str]:
    return list(dict.fromkeys(ID_PATTERN.findall(text)))


@dataclass(frozen=True)
class VerificationReport:
    kept: int
    dropped: int
    reasons: tuple[str, ...] = ()

    @property
    def rate(self) -> float:
        total = self.kept + self.dropped
        return self.kept / total if total else 0.0

    def to_dict(self) -> dict[str, object]:
        return {
            "kept": self.kept,
            "dropped": self.dropped,
            "rate": self.rate,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class VerifiedText:
    text: str
    evidence_ids: list[str]
    report: VerificationReport


async def verify(
    text: str,
    store: RecordStore,
    *,
    allowed_ids: set[str] | None = None,
    paper_ids: set[str] | None = None,
) -> VerifiedText:
    """Paper IDs must come from retrieved corpus documents, never model assertions.

    allowed_ids additionally limits citations to evidence actually shown to the provider.
    Emotion claims are dropped rather than replaced with invented behavioral claims.
    """
    kept: list[str] = []
    reasons: list[str] = []
    existence: dict[str, bool] = {}
    for sentence in split_sentences(text):
        ids = extract_ids(sentence)
        reason = None
        if any(expression in sentence for expression in BANNED):
            reason = "banned_expression"
        elif not ids:
            reason = "missing_id"
        else:
            for evidence_id in ids:
                if allowed_ids is not None and evidence_id not in allowed_ids:
                    reason = "unseen_id"
                    break
                if evidence_id not in existence:
                    existence[evidence_id] = evidence_id in (
                        paper_ids or set()
                    ) or await store.exists(evidence_id)
                if not existence[evidence_id]:
                    reason = "unknown_id"
                    break
        if reason:
            reasons.append(reason)
        else:
            kept.append(sentence)
    result = "".join(kept)
    return VerifiedText(
        result, extract_ids(result), VerificationReport(len(kept), len(reasons), tuple(reasons))
    )
