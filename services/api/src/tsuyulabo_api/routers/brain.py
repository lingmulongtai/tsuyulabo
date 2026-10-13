from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from starlette.concurrency import run_in_threadpool
from tsuyulabo_api.db.base import new_id
from tsuyulabo_api.db.models import Adult, CareEvent, LarvaState, Week
from tsuyulabo_api.domain.genetics import phenotypes
from tsuyulabo_api.errors import APIError
from tsuyulabo_api.routers.zukan import BEHAVIORS
from tsuyulabo_api.services import week as week_service
from tsuyulabo_api.services.brain_activity import ActivityCache, BrainActivity, Scenario
from tsuyulabo_api.services.brain_state import snapshot as brain_snapshot
from tsuyulabo_api.services.clock import game_now
from tsuyulabo_api.services.dispatch import enqueue
from tsuyulabo_api.services.game import Brain, CurrentClock, CurrentUser, Session, record_care, rng
from tsuyulabo_api.services.idempotency import IdempotentRoute

router = APIRouter(prefix="/v1/flies", route_class=IdempotentRoute)


class ExperimentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["odor_choice"] = "odor_choice"
    cue: Literal["banana", "apple_vinegar", "yeast", "grape", "blue_light"] = "banana"
    trials: int = Field(default=100, ge=1, le=1000, strict=True)


async def fly_state(
    fly_id: str, user: CurrentUser, session: Session, clock: CurrentClock
) -> tuple[dict, dict]:
    adult = await session.get(Adult, fly_id)
    if adult is not None and adult.user_id == user.id:
        return brain_snapshot(adult), {"stage": "adult", "energy": adult.energy}
    week = await session.get(Week, fly_id)
    if week is None or week.user_id != user.id or week.status != "active":
        raise APIError("not_found", "個体が見つかりません", 404)
    larva = await week_service.evaluate(session, week, game_now(clock, user))
    return brain_snapshot(larva), week_service.state_stats(larva).display() | {"stage": larva.stage}


@router.get("/{fly_id}/behavior")
async def behavior(
    fly_id: str,
    user: CurrentUser,
    session: Session,
    clock: CurrentClock,
    brain: Brain,
    scenario: str = Query(
        default="rest",
        pattern="^(rest|sugar|bitter|sugar\\+bitter|looming|light_left|light_right|antenna_touch|liked_odor|disliked_odor)$",
    ),
) -> dict[str, float]:
    snapshot, context = await fly_state(fly_id, user, session, clock)
    probabilities = brain.behavior(snapshot, context | {"scenario": scenario})
    if probabilities:
        observed = max(probabilities, key=probabilities.get)
        if observed in BEHAVIORS:
            user.observed_behaviors = sorted(set(user.observed_behaviors) | {observed})
        adult = await session.get(Adult, fly_id)
        week = await session.get(Week, adult.week_id if adult else fly_id)
        now = game_now(clock, user)
        latest = await session.scalar(
            select(CareEvent)
            .where(
                CareEvent.user_id == user.id,
                CareEvent.week_id == week.id,
                CareEvent.kind == "behaviour",
            )
            .order_by(CareEvent.created_at.desc(), CareEvent.seq.desc())
            .limit(1)
        )
        # Keep the current output fresh without recording every animation frame.
        if (
            latest is None
            or latest.payload.get("behaviour") != observed
            or (now - latest.created_at).total_seconds() >= 60
        ):
            larva = await session.get(LarvaState, week.id)
            await record_care(
                session,
                user.id,
                week.id,
                week.started_at,
                now,
                "behaviour",
                {
                    "behaviour": observed,
                    "stage": context["stage"],
                    "scenario": scenario,
                    "environment": larva.vial if larva and not adult else {},
                    "source": "brain_decoder",
                    "fly_id": fly_id,
                    "sex": adult.sex.lower() if adult else None,
                    "phenotypes": phenotypes(adult.genotype) if adult else [],
                },
            )
    return probabilities


@router.get("/{fly_id}/brain/activity", response_model=BrainActivity)
async def activity(
    fly_id: str,
    request: Request,
    user: CurrentUser,
    session: Session,
    clock: CurrentClock,
    brain: Brain,
    scenario: Scenario = "sugar",
) -> BrainActivity:
    """Observe a copy of an owned adult or active week's larva, in 20 equal windows."""
    snapshot, _ = await fly_state(fly_id, user, session, clock)
    if not hasattr(request.app.state, "brain_activity_cache"):
        request.app.state.brain_activity_cache = ActivityCache()
    cache: ActivityCache = request.app.state.brain_activity_cache
    return await run_in_threadpool(cache.get, brain, user.id, fly_id, snapshot, scenario)


@router.post("/{fly_id}/experiments", status_code=202)
async def experiment(
    fly_id: str,
    body: ExperimentRequest,
    request: Request,
    tasks: BackgroundTasks,
    user: CurrentUser,
    session: Session,
    clock: CurrentClock,
) -> dict[str, str]:
    snapshot, _ = await fly_state(fly_id, user, session, clock)
    adult = await session.get(Adult, fly_id)
    week_id = adult.week_id if adult is not None else fly_id
    records = await session.scalars(
        select(CareEvent).where(CareEvent.week_id == week_id, CareEvent.kind == "training")
    )
    if any(event.payload.get("learning_status") == "pending" for event in records):
        raise APIError("learning_pending", "しつけを覚えているところです。少し待ってください", 409)
    params = body.model_dump() | {
        "user_id": user.id,
        "fly_id": fly_id,
        "snapshot": snapshot,
        "seed": rng().getrandbits(63),
        "experiment_id": new_id(),
        "created_at": game_now(clock, user).isoformat(),
    }
    job = await enqueue(session, request, tasks, user.id, "brain.experiment", params)
    return {"job_id": job.id}
