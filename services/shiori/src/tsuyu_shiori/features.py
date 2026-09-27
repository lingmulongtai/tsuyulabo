from __future__ import annotations

from datetime import UTC, datetime, timedelta, timezone

from tsuyu_shiori.agent import Answer, run_agent
from tsuyu_shiori.gateway import Provider
from tsuyu_shiori.rag import Retriever
from tsuyu_shiori.records import Lab, RecordStore
from tsuyu_shiori.tools import ToolContext

JST = timezone(timedelta(hours=9))


async def answer_question(
    question: str,
    *,
    store: RecordStore,
    lab: Lab,
    week_id: str,
    fly_id: str,
    provider: Provider | None = None,
    retriever: Retriever | None = None,
) -> Answer:
    context = ToolContext(store, lab, week_id, fly_id)
    if retriever is not None:
        context.retriever = retriever
    return await run_agent(question, context, provider=provider)


async def morning_memo(
    *,
    store: RecordStore,
    lab: Lab,
    week_id: str,
    fly_id: str,
    now: datetime | None = None,
    provider: Provider | None = None,
) -> Answer:
    now = now or datetime.now(UTC)
    if now.tzinfo is None:
        raise ValueError("now must be timezone-aware")
    today = now.astimezone(JST).replace(hour=0, minute=0, second=0, microsecond=0)
    context = ToolContext(
        store,
        lab,
        week_id,
        fly_id,
        care_since=(today - timedelta(days=1)).isoformat(),
        care_until=today.isoformat(),
        sleep_since=(today - timedelta(hours=12)).isoformat(),
    )
    return await run_agent(
        "前日のお世話と前夜の睡眠の朝のメモをお願いします。",
        context,
        provider=provider,
        feature="morning",
        purpose="journal",
        max_sentences=3,
    )


async def coach_tip(
    *,
    store: RecordStore,
    lab: Lab,
    week_id: str,
    fly_id: str,
    cue: str = "banana",
    provider: Provider | None = None,
) -> Answer:
    return await run_agent(
        f"{cue}の好みと今週の記録を使ってコーチしてください。",
        ToolContext(store, lab, week_id, fly_id),
        provider=provider,
        feature="coach",
        max_sentences=1,
    )


async def presentation_host(
    *,
    store: RecordStore,
    lab: Lab,
    week_id: str,
    fly_id: str,
    provider: Provider | None = None,
) -> Answer:
    """The host supplies rank as a persisted presentation care record (data.rank)."""
    return await run_agent(
        "1週間のお世話と記録されたランクを研究発表会でふり返ってください。",
        ToolContext(store, lab, week_id, fly_id),
        provider=provider,
        feature="presentation",
    )
