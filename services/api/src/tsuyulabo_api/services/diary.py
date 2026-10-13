"""Generate a day's entry once, retaining real record IDs and the selected moment."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tsuyu_shiori.companion import diary_entry
from tsuyu_shiori.diary_events import notable_events
from tsuyu_shiori.features import JST
from tsuyu_shiori.gateway import Provider
from tsuyulabo_api.db.models import DiaryEntry, User
from tsuyulabo_api.domain.lifecycle import stage_at
from tsuyulabo_api.services.shiori_store import SQLRecordStore


def payload(entry: DiaryEntry) -> dict[str, Any]:
    return {
        "id": entry.id,
        "week_id": entry.week_id,
        "day": entry.day.isoformat(),
        "text": entry.text,
        "evidence": entry.evidence,
        "snapshot": entry.snapshot,
        "ai_label": "AI",
    }


async def generate(
    session: AsyncSession,
    user_id: str,
    week_id: str,
    day: date,
    *,
    provider: Provider | None = None,
) -> dict[str, Any]:
    await session.scalar(select(User).where(User.id == user_id).with_for_update())
    store = SQLRecordStore(session, user_id)
    week = await store.week(week_id)
    existing = await session.scalar(
        select(DiaryEntry).where(
            DiaryEntry.user_id == user_id,
            DiaryEntry.week_id == week_id,
            DiaryEntry.day == day,
        )
    )
    if existing:
        return {"reused": True, "entry": payload(existing)}
    start = datetime.combine(day, datetime.min.time(), JST)
    records = await store.care_events(week_id)
    for record in records:
        if record.occurred_at is not None and record.occurred_at >= week.started_at:
            record.data.setdefault(
                "stage",
                "adult"
                if record.kind == "eclosion"
                else stage_at(week.started_at, record.occurred_at),
            )
            record.data.setdefault("environment", record.data.get("vial", {}))
            record.data.setdefault("growth_delta", record.data.get("effects", {}).get("growth", 0))
    moments = notable_events(records, start, start + timedelta(days=1))
    if not moments:
        return {"skipped": "no_observations"}
    answer = await diary_entry(moments, store, provider=provider)
    if answer.empty_state:
        return {"skipped": "no_verified_text"}
    entry = DiaryEntry(
        user_id=user_id,
        week_id=week_id,
        day=day,
        text=answer.text,
        evidence=answer.evidence_ids,
        snapshot=moments[0].snapshot,
    )
    session.add(entry)
    await session.flush()
    return {"reused": False, "entry": payload(entry)}


async def history(session: AsyncSession, user_id: str, fly_id: str) -> list[dict[str, Any]]:
    week, _ = await SQLRecordStore(session, user_id).fly_week(fly_id)
    entries = await session.scalars(
        select(DiaryEntry)
        .where(
            DiaryEntry.user_id == user_id,
            DiaryEntry.week_id == week.id,
        )
        .order_by(DiaryEntry.day.desc())
        .limit(366)
    )
    return [payload(entry) for entry in entries]
