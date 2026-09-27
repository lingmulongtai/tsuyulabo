from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tsuyulabo_api.brain_adapter import BrainAdapter
from tsuyulabo_api.db.models import Experiment, User
from tsuyulabo_api.services.jobs import JobFunction


def handler(sessions: async_sessionmaker[AsyncSession], brain: BrainAdapter) -> JobFunction:
    async def run(params: dict[str, Any]) -> dict[str, Any]:
        result = brain.experiment(
            params["snapshot"], params["cue"], params["trials"], params["seed"]
        )
        async with sessions() as session, session.begin():
            await session.scalar(select(User).where(User.id == params["user_id"]).with_for_update())
            # The persisted experiment ID makes queue redelivery safe for evidence records.
            existing = await session.get(Experiment, params["experiment_id"])
            if existing:
                return {
                    "experiment_id": existing.id,
                    "seq": existing.seq,
                    "display_id": f"c-{existing.seq}",
                    "result": existing.result,
                }
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
        return {
            "experiment_id": experiment.id,
            "seq": seq,
            "display_id": f"c-{seq}",
            "result": result,
        }

    return run
