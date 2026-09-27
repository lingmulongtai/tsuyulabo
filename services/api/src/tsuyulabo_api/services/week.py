from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tsuyulabo_api.db.models import Adult, CareEvent, LarvaState, Puzzle, TeamSlot, Week
from tsuyulabo_api.domain import adults, care_miss, lifecycle, presentation, stats
from tsuyulabo_api.domain.clock import research_day
from tsuyulabo_api.domain.events import CareEvent as DomainEvent
from tsuyulabo_api.domain.puzzles import pupation_site
from tsuyulabo_api.errors import APIError
from tsuyulabo_api.services.game import record_care, rng


async def current(session: AsyncSession, user_id: str) -> Week:
    week = await session.scalar(
        select(Week).where(Week.user_id == user_id, Week.status == "active")
    )
    if week is None:
        raise APIError("no_active_week", "育成中の週がありません", 409)
    return week


async def events(session: AsyncSession, week: Week) -> list[CareEvent]:
    return list(
        await session.scalars(
            select(CareEvent).where(CareEvent.week_id == week.id).order_by(CareEvent.seq)
        )
    )


def domain_events(records: list[CareEvent]) -> list[DomainEvent]:
    return [
        DomainEvent(
            at=e.created_at,
            kind=e.kind,
            score=int(e.score or 0),
            **{
                key: e.payload.get(key, default)
                for key, default in (
                    ("stars", 0),
                    ("great_success", False),
                    ("hirameki", False),
                    ("hit", False),
                )
            },
        )
        for e in records
    ]


def state_stats(state: LarvaState) -> stats.Stats:
    return stats.Stats(
        state.last_computed_at,
        state.hunger,
        state.cleanliness,
        state.stage != "egg",
        state.hunger_zero_since,
    )


async def evaluate(session: AsyncSession, week: Week, now: datetime) -> LarvaState:
    state = await session.get(LarvaState, week.id)
    # Dev reset may move time backwards. Never decay twice or undo past effects.
    if now < state.last_computed_at:
        raise APIError("time_reversed", "時刻を前回の計算時刻以降に進めてください", 409)
    log = domain_events(await events(session, week))
    keys = {tuple(key) for key in state.miss_keys}
    keys |= care_miss.evaluate(week.started_at, state.last_computed_at, now, log)
    state.miss_keys = [list(key) for key in sorted(keys, key=str)]
    week.care_miss = len(keys)
    computed = stats.decay(state_stats(state), week.started_at, now)
    state.hunger, state.cleanliness = computed.hunger, computed.cleanliness
    state.hunger_zero_since = computed.hunger_zero_since
    state.last_computed_at = now
    state.stage = lifecycle.stage_at(week.started_at, now)
    if ("pupation_site", 5, None) in keys and not any(e.kind == "pupation_default" for e in log):
        puzzle = await session.scalar(
            select(Puzzle)
            .where(Puzzle.week_id == week.id, Puzzle.kind == "pupation_site")
            .order_by(Puzzle.issued_at.desc())
            .limit(1)
        )
        params = puzzle.params if puzzle else pupation_site.generate(rng(), {})[0]
        await record_care(
            session,
            week.user_id,
            week.id,
            week.started_at,
            now,
            "pupation_default",
            {"choice": care_miss.default_pupation_choice(params["options"])},
        )
    summary = presentation.summarize(log, keys)
    week.points, week.rank = summary.points, summary.rank
    await session.flush()
    return state


async def team_bonus(session: AsyncSession, user_id: str) -> dict[str, float]:
    members = await session.scalars(
        select(Adult)
        .join(TeamSlot, TeamSlot.adult_id == Adult.id)
        .where(TeamSlot.user_id == user_id)
    )
    return adults.bonuses(skill for member in members for skill in member.subskills)


async def presentation_payload(session: AsyncSession, week: Week, now: datetime) -> dict[str, Any]:
    state = await evaluate(session, week, now)
    summary = presentation.summarize(
        domain_events(await events(session, week)),
        (tuple(key) for key in state.miss_keys),
        (await team_bonus(session, week.user_id))["rp_bonus"],
    )
    return asdict(summary)


async def payload(session: AsyncSession, week: Week, now: datetime) -> dict[str, Any]:
    state = await evaluate(session, week, now)
    records = await events(session, week)
    return {
        "id": week.id,
        "started_at": week.started_at,
        "status": week.status,
        "research_day": research_day(week.started_at, now),
        "stage": state.stage,
        "ready_to_eclose": lifecycle.ready_to_eclose(week.started_at, now),
        "care_miss": week.care_miss,
        "points_so_far": week.points,
        "fly": state_stats(state).display() | {"stage": state.stage, "growth": state.growth},
        "days": [
            {
                "research_day": day,
                "events": [
                    {
                        "id": e.id,
                        "seq": e.seq,
                        "kind": e.kind,
                        "slot": e.slot,
                        "score": e.score,
                        "payload": e.payload,
                        "created_at": e.created_at,
                    }
                    for e in records
                    if e.research_day == day
                ],
            }
            for day in range(1, 8)
        ],
    }
