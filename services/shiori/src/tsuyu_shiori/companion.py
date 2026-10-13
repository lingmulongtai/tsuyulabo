"""Evidence-first companion intents, independently gated until LoRA v3 acceptance."""

from __future__ import annotations

import json
import os
from typing import Any

from tsuyu_shiori.agent import Answer
from tsuyu_shiori.agent.prompt import SYSTEM_PROMPT
from tsuyu_shiori.diary_events import Moment
from tsuyu_shiori.gateway import MockProvider, Provider, default_provider
from tsuyu_shiori.hint_rules import Trouble
from tsuyu_shiori.records import RecordStore
from tsuyu_shiori.verify import verify


def intent_provider(intent: str, provider: Provider | None = None) -> Provider:
    accepted = os.getenv("SHIORI_ACCEPTED_INTENTS", "").split(",")
    if intent not in {item.strip() for item in accepted}:
        return MockProvider()
    return provider if provider is not None else default_provider()


async def phrase(
    intent: str,
    payload: dict[str, Any],
    store: RecordStore,
    evidence: list[str],
    *,
    provider: Provider | None = None,
    evaluate_candidate: bool = False,
) -> Answer:
    selected = (
        provider
        if evaluate_candidate and provider is not None
        else intent_provider(intent, provider)
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": json.dumps({"feature": intent, **payload}, ensure_ascii=False)},
    ]
    response = await selected.complete(messages, [], selected.model_for("journal"))
    calls = [response.cost]
    checked = await verify(response.text, store, allowed_ids=set(evidence))
    fallback = False
    native = checked
    if not checked.text or checked.report.dropped:
        fallback = True
        response = await MockProvider().complete(messages, [], "mock-journal")
        calls.append(response.cost)
        checked = await verify(response.text, store, allowed_ids=set(evidence))
    return Answer(
        checked.text,
        checked.evidence_ids,
        checked.report,
        calls=calls,
        fallback_used=fallback,
        provider_text=native.text,
        provider_verification=native.report,
        stopped_reason="fallback" if fallback else "final",
        empty_state=not checked.text,
    )


async def diary_entry(
    moments: list[Moment],
    store: RecordStore,
    *,
    provider: Provider | None = None,
    evaluate_candidate: bool = False,
) -> Answer:
    return await phrase(
        "diary",
        {"moments": [{"description": m.description, "evidence": m.evidence} for m in moments]},
        store,
        [i for m in moments for i in m.evidence],
        provider=provider,
        evaluate_candidate=evaluate_candidate,
    )


async def quiet_hint(
    trouble: Trouble,
    evidence_id: str,
    store: RecordStore,
    *,
    provider: Provider | None = None,
    evaluate_candidate: bool = False,
) -> Answer:
    return await phrase(
        "hint",
        {"observation": trouble.observation, "help": trouble.help, "evidence": [evidence_id]},
        store,
        [evidence_id],
        provider=provider,
        evaluate_candidate=evaluate_candidate,
    )
