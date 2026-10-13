"""Explain the last displayed brain output using an owned individual's care tools."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tsuyu_shiori.agent import run_agent
from tsuyu_shiori.companion import intent_provider, phrase
from tsuyu_shiori.tools import ToolContext
from tsuyu_shiori.verify import split_sentences
from tsuyulabo_api.db.models import CareEvent
from tsuyulabo_api.services.shiori_brain import BrainEngine
from tsuyulabo_api.services.shiori_store import SQLLab, SQLRecordStore

LABELS = {
    "rest": "休む",
    "walk": "歩く",
    "feed": "食べる",
    "groom": "毛づくろいする",
    "approach": "寄っていく",
    "avoid": "離れる",
    "escape": "逃げる",
    "turn_left": "左を向く",
    "turn_right": "右を向く",
    "fly": "飛ぶ",
}


async def explain(
    session: AsyncSession,
    user_id: str,
    fly_id: str,
    now: datetime,
    *,
    behaviour: str | None = None,
    source: str = "brain_decoder",
    brain: BrainEngine | None = None,
) -> dict[str, Any]:
    store = SQLRecordStore(session, user_id)
    week, _ = await store.fly_week(fly_id)
    event = await session.scalar(
        select(CareEvent)
        .where(
            CareEvent.user_id == user_id,
            CareEvent.week_id == week.id,
            CareEvent.kind == "behaviour",
            CareEvent.payload["source"].as_string() == source,
            CareEvent.created_at >= now - timedelta(minutes=2),
            CareEvent.created_at <= now,
        )
        .order_by(CareEvent.created_at.desc(), CareEvent.seq.desc())
        .limit(1)
    )
    if event is None:
        raise ValueError("no recent behaviour")
    if event.payload.get("fly_id") != fly_id:
        raise ValueError("no recent behaviour for this individual")
    action = event.payload["behaviour"]
    if behaviour is not None and action != behaviour:
        raise ValueError("behaviour has changed")
    cue = event.payload.get("cue")
    question = f"どうして{cue}の好みに反応するの？" if cue else "最近のしつけの好みは？"
    answer = await run_agent(
        question,
        ToolContext(store, SQLLab(session, user_id, brain), week.id, fly_id),
        provider=intent_provider("behaviour-why"),
        max_sentences=3,
    )
    ref = f"#{event.seq:04}"
    context_text = (
        next(
            (
                sentence
                for sentence in split_sentences(answer.text)
                if "好み" in sentence or "連合" in sentence
            ),
            split_sentences(answer.text)[0],
        )
        if not answer.empty_state
        else f"理由を絞るには、好き嫌いのお世話記録がまだ足りません {ref}。"
    )
    phrased = await phrase(
        "behaviour-why",
        {
            "observation": {
                "id": ref,
                "behaviour": action,
                "label": LABELS.get(action, "動く"),
                "source": source,
            },
            "context_text": context_text,
            "context_evidence": answer.evidence_ids,
        },
        store,
        [ref, *answer.evidence_ids],
    )
    return answer.to_dict() | {
        "text": phrased.text,
        "answer": phrased.text,
        "evidence": phrased.evidence_ids,
        "verification": phrased.verification.to_dict(),
        "observation_id": ref,
    }
