"""Queued learning applies accepted care events in their per-user sequence order."""

from __future__ import annotations

import asyncio
from typing import Any

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tsuyulabo_api.brain_adapter import BrainAdapter
from tsuyulabo_api.db.models import Adult, CareEvent, Job, LarvaState, Puzzle, User, Week
from tsuyulabo_api.domain.puzzles.training import skill_unlocked
from tsuyulabo_api.services.brain_state import snapshot, store
from tsuyulabo_api.services.dispatch import dispatch
from tsuyulabo_api.services.jobs import JobFunction, create_job, finish_job


async def apply_pending(
    session: AsyncSession, brain: BrainAdapter, params: dict[str, Any]
) -> dict[str, Any]:
    await session.scalar(select(User).where(User.id == params["user_id"]).with_for_update())
    target = await session.scalar(
        select(CareEvent).where(
            CareEvent.id == params["event_id"], CareEvent.user_id == params["user_id"]
        )
    )
    if target is None or target.kind != "training":
        raise ValueError("training event not found")
    records = await session.scalars(
        select(CareEvent)
        .where(
            CareEvent.week_id == target.week_id,
            CareEvent.kind == "training",
            CareEvent.seq <= target.seq,
        )
        .order_by(CareEvent.seq)
    )
    larva = await session.get(LarvaState, target.week_id)
    week = await session.get(Week, target.week_id)
    adult = await session.get(Adult, week.adult_id) if week.adult_id else None
    for event in records:
        if event.payload.get("learning_status") != "pending":
            continue
        job = await session.get(Job, event.payload["job_id"])
        inputs = job.params
        arguments = {key: inputs[key] for key in ("cue", "valence", "strength", "seed")}
        learned, value = await asyncio.to_thread(brain.train, snapshot(larva), **arguments)
        await asyncio.to_thread(store, larva, learned, brain)
        skill = skill_unlocked(inputs["cue"], value)
        unlocked = skill if skill and skill not in larva.skills else None
        if skill:
            larva.skills = larva.skills | {skill: True}
        if adult is not None:
            learned, _ = await asyncio.to_thread(brain.train, snapshot(adult), **arguments)
            await asyncio.to_thread(store, adult, learned, brain)
            adult.skills = adult.skills | larva.skills
        result = event.payload | {
            "learning_status": "completed",
            "skill_unlocked": unlocked,
            "association": {
                "cue": inputs["cue"],
                "valence": inputs["valence"],
                "value": value,
            },
        }
        event.payload = result
        puzzle = await session.get(Puzzle, inputs["puzzle_id"])
        puzzle.result = result
        await finish_job(session, job, result=result)
    return target.payload


def handler(sessions: async_sessionmaker[AsyncSession], brain: BrainAdapter) -> JobFunction:
    async def run(params: dict[str, Any]) -> dict[str, Any]:
        async with sessions() as session, session.begin():
            return await apply_pending(session, brain, params)

    return run


async def prepare(
    session: AsyncSession,
    request: Request,
    user_id: str,
    event: CareEvent,
    puzzle: Puzzle,
    arguments: dict[str, Any],
    result: dict[str, Any],
) -> dict[str, Any]:
    job = await create_job(session, user_id, "brain.training")
    job.params = arguments | {"user_id": user_id, "event_id": event.id, "puzzle_id": puzzle.id}
    result = result | {"job_id": job.id, "learning_status": "pending"}
    event.payload = result
    params = job.params

    async def after_commit() -> dict[str, Any] | None:
        await dispatch(request, job.id, job.kind, params)
        # Stop polling after the response deadline. The durable job remains pending
        # and the worker can still finish it; GET /jobs and week reads expose it.
        for _ in range(60):
            async with request.app.state.session_factory() as connection:
                stored = await connection.get(Job, job.id)
                if stored.status == "succeeded":
                    return stored.result
                if stored.status == "failed":
                    return result | {"learning_status": "failed"}
            await asyncio.sleep(0.05)
        return None

    request.state.after_commit = after_commit
    return result
