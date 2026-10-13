from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tsuyulabo_api.brain_adapter import BrainAdapter
from tsuyulabo_api.db.models import Adult, Experiment, LarvaState, User, Week
from tsuyulabo_api.domain.genetics import phenotypes
from tsuyulabo_api.services.game import record_care
from tsuyulabo_api.services.jobs import JobFunction


async def perform(
    session: AsyncSession, brain: BrainAdapter, params: dict[str, Any]
) -> dict[str, Any]:
    await session.scalar(select(User).where(User.id == params["user_id"]).with_for_update())
    # The persisted experiment ID makes queue redelivery safe for evidence records.
    existing = await session.get(Experiment, params["experiment_id"])
    if existing:
        if existing.user_id != params["user_id"] or existing.adult_or_week_id != params["fly_id"]:
            raise ValueError("experiment does not belong to this user and fly")
        return {
            "experiment_id": existing.id,
            "seq": existing.seq,
            "display_id": f"c-{existing.seq}",
            "result": existing.result,
        }
    result = await asyncio.to_thread(
        brain.experiment, params["snapshot"], params["cue"], params["trials"], params["seed"]
    )
    seq = (
        await session.scalar(
            select(func.max(Experiment.seq)).where(Experiment.user_id == params["user_id"])
        )
        or 0
    ) + 1
    experiment = Experiment(
        id=params["experiment_id"],
        user_id=params["user_id"],
        adult_or_week_id=params["fly_id"],
        kind="odor_choice",
        seq=seq,
        params={key: params[key] for key in ("cue", "trials", "seed")},
        result=result,
        created_at=datetime.fromisoformat(params["created_at"]),
    )
    session.add(experiment)
    if params["trials"] == 1 and result.get("toward", 0) + result.get("away", 0) == 1:
        adult = await session.get(Adult, params["fly_id"])
        week = await session.get(Week, adult.week_id if adult else params["fly_id"])
        if week is not None and week.user_id == params["user_id"]:
            larva = await session.get(LarvaState, week.id)
            action = "approach" if result["toward"] > result["away"] else "avoid"
            await record_care(
                session,
                params["user_id"],
                week.id,
                week.started_at,
                experiment.created_at,
                "behaviour",
                {
                    "behaviour": action,
                    "cue": params["cue"],
                    "source": "copy_odor_choice",
                    "experiment_evidence": f"#c-{seq}",
                    "fly_id": params["fly_id"],
                    "stage": "adult" if adult else larva.stage if larva else "egg",
                    "environment": larva.vial if larva and not adult else {},
                    "sex": adult.sex.lower() if adult else None,
                    "phenotypes": phenotypes(adult.genotype) if adult else [],
                },
            )
    return {
        "experiment_id": experiment.id,
        "seq": seq,
        "display_id": f"c-{seq}",
        "result": result,
    }


def handler(sessions: async_sessionmaker[AsyncSession], brain: BrainAdapter) -> JobFunction:
    async def run(params: dict[str, Any]) -> dict[str, Any]:
        async with sessions() as session, session.begin():
            return await perform(session, brain, params)

    return run
