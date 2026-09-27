from __future__ import annotations

import asyncio
import re
from copy import deepcopy
from datetime import timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from tsuyu_shiori.records import Record
from tsuyu_shiori.tools import ExperimentArguments
from tsuyulabo_api.db.models import (
    Adult,
    CareEvent,
    Experiment,
    LarvaState,
    SleepSession,
    User,
    Week,
)

from .shiori_brain import BrainEngine, BrainSnapshot, RealBrainEngine


def care_record(event: CareEvent, fly_id: str | None = None) -> Record:
    data = deepcopy(event.payload)
    # API training records nest cue/valence/value under association; tools filter
    # the normalized fields without changing the persisted audit event.
    association = data.get("association") or {}
    for name in ("cue", "valence", "value"):
        if name in association:
            data.setdefault(name, association[name])
    return Record(
        f"#{event.seq:04}",
        event.kind,
        {**data, "research_day": event.research_day, "score": event.score},
        event.week_id,
        fly_id or event.week_id,
        event.created_at,
    )


def experiment_record(experiment: Experiment) -> Record:
    return Record(
        f"#c-{experiment.seq}",
        "experiment",
        {**deepcopy(experiment.params), **deepcopy(experiment.result or {})},
        fly_id=experiment.adult_or_week_id,
        occurred_at=experiment.created_at,
    )


class SQLRecordStore:
    def __init__(self, session: AsyncSession, user_id: str) -> None:
        self.session, self.user_id = session, user_id

    async def week(self, week_id: str) -> Week:
        week = await self.session.scalar(
            select(Week).where(Week.id == week_id, Week.user_id == self.user_id)
        )
        if week is None:
            raise ValueError("week not found")
        return week

    async def fly_week(self, fly_id: str) -> tuple[Week, Adult | None]:
        adult = await self.session.scalar(
            select(Adult).where(Adult.id == fly_id, Adult.user_id == self.user_id)
        )
        return await self.week(adult.week_id if adult else fly_id), adult

    async def care_events(self, week_id: str, kinds: list[str] | None = None) -> list[Record]:
        await self.week(week_id)
        query = select(CareEvent).where(
            CareEvent.user_id == self.user_id, CareEvent.week_id == week_id
        )
        if kinds is not None:
            query = query.where(CareEvent.kind.in_(kinds))
        events = await self.session.scalars(query.order_by(CareEvent.created_at, CareEvent.seq))
        return [care_record(event) for event in events]

    async def sleep_sessions(self, week_id: str) -> list[Record]:
        week = await self.week(week_id)
        next_start = await self.session.scalar(
            select(func.min(Week.started_at)).where(
                Week.user_id == self.user_id, Week.started_at > week.started_at
            )
        )
        end = week.eclosed_at or next_start or week.started_at + timedelta(days=7)
        rows = await self.session.scalars(
            select(SleepSession)
            .where(
                SleepSession.user_id == self.user_id,
                SleepSession.started_at >= week.started_at,
                SleepSession.started_at < end,
            )
            .order_by(SleepSession.started_at)
        )
        return [
            Record(
                f"#s-{row.id}",
                "sleep",
                {
                    "hours": (
                        (row.ended_at - row.started_at).total_seconds() / 3600
                        if row.ended_at
                        else None
                    ),
                    "bonus": row.bonus,
                    "ended_at": row.ended_at.isoformat() if row.ended_at else None,
                },
                week_id,
                occurred_at=row.started_at,
            )
            for row in rows
        ]

    async def association(self, fly_id: str, cue: str) -> Record | None:
        week, _ = await self.fly_week(fly_id)
        records = await self.care_events(week.id, ["training"])
        for record in reversed(records):
            association = record.data.get("association") or {}
            if record.data.get("cue", association.get("cue")) != cue:
                continue
            value = record.data.get(
                "association_value", record.data.get("value", association.get("value"))
            )
            if value is not None:
                return Record(
                    record.id,
                    "association",
                    {**record.data, "value": value},
                    week.id,
                    fly_id,
                    record.occurred_at,
                )
        return None

    async def experiment(self, evidence_id: str) -> Record | None:
        if not re.fullmatch(r"#c-[1-9]\d*", evidence_id):
            return None
        row = await self.session.scalar(
            select(Experiment).where(
                Experiment.user_id == self.user_id, Experiment.seq == int(evidence_id[3:])
            )
        )
        return experiment_record(row) if row else None

    async def exists(self, evidence_id: str) -> bool:
        if evidence_id.startswith("#c-"):
            return await self.experiment(evidence_id) is not None
        if evidence_id.startswith("#s-"):
            return (
                await self.session.scalar(
                    select(SleepSession.id).where(
                        SleepSession.id == evidence_id[3:], SleepSession.user_id == self.user_id
                    )
                )
                is not None
            )
        if re.fullmatch(r"#\d+", evidence_id):
            seq = int(evidence_id[1:])
            if evidence_id != f"#{seq:04}":
                return False
            return (
                await self.session.scalar(
                    select(CareEvent.id).where(
                        CareEvent.user_id == self.user_id, CareEvent.seq == seq
                    )
                )
                is not None
            )
        return False


class SQLLab:
    def __init__(
        self, session: AsyncSession, user_id: str, brain: BrainEngine | None = None
    ) -> None:
        self.session, self.user_id = session, user_id
        self.store = SQLRecordStore(session, user_id)
        self.brain = brain if brain is not None else RealBrainEngine()

    async def snapshot(self, fly_id: str) -> BrainSnapshot:
        week, adult = await self.store.fly_week(fly_id)
        training = await self.store.care_events(week.id, ["training"])
        row = adult or await self.session.get(LarvaState, week.id)
        return BrainSnapshot(
            fly_id,
            deepcopy(row.brain_params) if row else {},
            bytes(row.learned_weights) if row and row.learned_weights else None,
            [deepcopy(r.data) for r in training],
            list(adult.traits) if adult else [],
            adult.sex.lower() if adult else "f",
            deepcopy(row.brain_snapshot) if row else {},
        )

    async def run_odor_choice(
        self, fly_id: str, cue: str, trials: int = 20, seed: int = 0
    ) -> Record:
        ExperimentArguments.model_validate(
            {"fly_id": fly_id, "cue": cue, "trials": trials, "seed": seed}
        )
        snapshot = await self.snapshot(fly_id)
        result = await asyncio.to_thread(self.brain.run_odor_choice, snapshot, cue, trials, seed)
        if any(type(result.get(key)) is not int or result[key] < 0 for key in ("toward", "away")):
            raise ValueError("brain returned invalid counts")
        if result["toward"] + result["away"] != trials:
            raise ValueError("brain counts do not match trials")
        # Serialize per-user sequence allocation across processes (SQLite uses BEGIN IMMEDIATE).
        await self.session.scalar(select(User).where(User.id == self.user_id).with_for_update())
        seq = await self.session.scalar(
            select(func.coalesce(func.max(Experiment.seq), 0)).where(
                Experiment.user_id == self.user_id
            )
        )
        row = Experiment(
            user_id=self.user_id,
            adult_or_week_id=fly_id,
            kind="odor_choice",
            params={"cue": cue, "trials": trials, "seed": seed},
            result={**result, "engine": type(self.brain).__name__},
            seq=(seq or 0) + 1,
        )
        self.session.add(row)
        await self.session.flush()
        return experiment_record(row)


async def conversation_scope(store: SQLRecordStore, params: dict[str, Any]) -> tuple[str, str]:
    """Resolve defaults while proving supplied week and fly belong to the same user/week."""
    week_id, fly_id = params.get("week_id"), params.get("fly_id")
    week: Week | None
    if fly_id:
        week, _ = await store.fly_week(fly_id)
        if week_id is not None and week_id != week.id:
            raise ValueError("fly and week do not match")
        return week.id, fly_id
    if week_id:
        week = await store.week(week_id)
    else:
        week = await store.session.scalar(
            select(Week)
            .where(Week.user_id == store.user_id, Week.status == "active")
            .order_by(Week.started_at.desc())
        )
        if week is None:
            raise ValueError("no active week")
    return week.id, week.adult_id or week.id
