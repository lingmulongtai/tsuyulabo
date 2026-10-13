"""Persist hint evidence and enforce a six-hour per-individual quiet period."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tsuyu_shiori.companion import quiet_hint
from tsuyu_shiori.hint_rules import detect_trouble
from tsuyulabo_api.db.models import CareEvent, QuietHint
from tsuyulabo_api.domain import vial
from tsuyulabo_api.services import week as week_service
from tsuyulabo_api.services.game import record_care
from tsuyulabo_api.services.shiori_store import SQLRecordStore

COOLDOWN = timedelta(hours=6)


def payload(hint: QuietHint) -> dict[str, Any]:
    return {"id": hint.id, "text": hint.text, "evidence": hint.evidence, "ai_label": "AI"}


async def current(
    session: AsyncSession,
    user_id: str,
    fly_id: str,
    now: datetime,
) -> dict[str, Any] | None:
    store = SQLRecordStore(session, user_id)
    week, adult = await store.fly_week(fly_id)
    if adult:
        # Adult habitat is not currently persisted; do not reuse the larva's food clock.
        return None
    if week.status != "active":
        return None
    state = await week_service.evaluate(session, week, now)
    if state.stage in {"egg", "pupa"}:
        return None
    measured = vial.settle(state.vial, now, state.hunger, state.cleanliness)
    recent = list(
        await session.scalars(
            select(CareEvent)
            .where(
                CareEvent.user_id == user_id,
                CareEvent.week_id == week.id,
                CareEvent.kind == "behaviour",
                CareEvent.created_at <= now,
                CareEvent.created_at >= now - timedelta(minutes=5),
            )
            .order_by(CareEvent.created_at.desc())
            .limit(2)
        )
    )
    if len(recent) == 2 and all(e.payload.get("behaviour") == "escape" for e in recent):
        measured = measured | {"behaviour": "escape"}
    trouble = detect_trouble(measured, now)
    if trouble is None:
        return None
    latest = await session.scalar(
        select(QuietHint)
        .where(
            QuietHint.user_id == user_id,
            QuietHint.week_id == week.id,
            QuietHint.created_at > now - COOLDOWN,
        )
        .order_by(QuietHint.created_at.desc())
        .limit(1)
    )
    if latest:
        return (
            payload(latest) if latest.dismissed_at is None and latest.kind == trouble.kind else None
        )
    record = await record_care(
        session,
        user_id,
        week.id,
        week.started_at,
        now,
        "habitat_observation",
        {"state": measured, "trouble": trouble.kind},
    )
    answer = await quiet_hint(trouble, f"#{record.seq:04}", store)
    if answer.empty_state:
        return None
    hint = QuietHint(
        user_id=user_id,
        week_id=week.id,
        kind=trouble.kind,
        text=answer.text,
        evidence=answer.evidence_ids,
        created_at=now,
    )
    session.add(hint)
    await session.flush()
    return payload(hint)


async def dismiss(session: AsyncSession, user_id: str, hint_id: str, now: datetime) -> None:
    hint = await session.scalar(
        select(QuietHint).where(
            QuietHint.id == hint_id,
            QuietHint.user_id == user_id,
        )
    )
    if hint is None:
        raise ValueError("hint not found")
    hint.dismissed_at = hint.dismissed_at or now
