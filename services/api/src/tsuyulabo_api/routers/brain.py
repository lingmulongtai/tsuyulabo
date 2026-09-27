from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from tsuyulabo_api.db.base import new_id
from tsuyulabo_api.db.models import Adult, Week
from tsuyulabo_api.errors import APIError
from tsuyulabo_api.routers.zukan import BEHAVIORS
from tsuyulabo_api.services import week as week_service
from tsuyulabo_api.services.brain_state import snapshot as brain_snapshot
from tsuyulabo_api.services.clock import game_now
from tsuyulabo_api.services.dispatch import enqueue
from tsuyulabo_api.services.game import Brain, CurrentClock, CurrentUser, Session, rng
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
    return probabilities


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
