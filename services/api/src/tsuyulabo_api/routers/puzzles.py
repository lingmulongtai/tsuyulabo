from __future__ import annotations

from datetime import timedelta
from typing import Any, Literal

from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, model_validator
from tsuyulabo_api.db.models import Puzzle
from tsuyulabo_api.domain import constants as c
from tsuyulabo_api.domain import lifecycle, stats
from tsuyulabo_api.domain.clock import research_day, slot_of
from tsuyulabo_api.domain.puzzles import cleaning, meal, pupation_site, temperature, training
from tsuyulabo_api.domain.puzzles.common import verify_wall_clock
from tsuyulabo_api.errors import APIError
from tsuyulabo_api.services import week as service
from tsuyulabo_api.services.brain_state import snapshot as brain_snapshot
from tsuyulabo_api.services.brain_state import store as store_brain
from tsuyulabo_api.services.clock import game_now
from tsuyulabo_api.services.game import Brain, CurrentClock, CurrentUser, Session, record_care, rng
from tsuyulabo_api.services.idempotency import IdempotentRoute

router = APIRouter(prefix="/v1/puzzles", route_class=IdempotentRoute)
MODULES = {
    "meal": meal,
    "training": training,
    "cleaning": cleaning,
    "temperature": temperature,
    "pupation_site": pupation_site,
}


class IssueRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["meal", "training", "cleaning", "temperature", "pupation_site"]
    cue: Literal["banana", "apple_vinegar", "yeast", "grape", "blue_light"] | None = None
    valence: Literal["reward", "punish"] | None = None

    @model_validator(mode="after")
    def training_fields(self) -> IssueRequest:
        if self.kind == "training" and (self.cue is None or self.valence is None):
            raise ValueError("training requires cue and valence")
        return self


async def check_available(session: Session, week: Any, now: Any, kind: str) -> None:
    todo = next(
        item
        for item in lifecycle.action_availability(
            week.started_at, now, service.domain_events(await service.events(session, week))
        )
        if item.action == kind
    )
    if todo.status == "done":
        code = "slot_already_used" if kind == "meal" else "daily_limit_reached"
        raise APIError(code, "このお世話は済んでいます", 409)
    if todo.status != "available":
        raise APIError("not_available_today", "今はこのお世話をできません", 409)


@router.post("", status_code=201)
async def issue(
    body: IssueRequest, user: CurrentUser, session: Session, clock: CurrentClock
) -> dict[str, Any]:
    week, now = await service.current(session, user.id), game_now(clock, user)
    await service.evaluate(session, week, now)
    await check_available(session, week, now, body.kind)
    day = research_day(week.started_at, now)
    params, secret = MODULES[body.kind].generate(rng(), body.model_dump() | {"research_day": day})
    # Keep game-window identity separate from real issue/expiry timestamps.
    secret = secret | {"research_day": day, "slot": slot_of(now)}
    puzzle = Puzzle(
        user_id=user.id,
        week_id=week.id,
        kind=body.kind,
        params=params,
        secret=secret,
        issued_at=clock.now(),
        expires_at=clock.now() + timedelta(milliseconds=c.PUZZLE_EXPIRY_MS),
    )
    session.add(puzzle)
    await session.flush()
    return {
        "puzzle_id": puzzle.id,
        "kind": puzzle.kind,
        "params": params,
        "issued_at": puzzle.issued_at,
        "expires_at": puzzle.expires_at,
    }


@router.post("/{puzzle_id}/submit")
async def submit(
    puzzle_id: str,
    body: dict[str, Any],
    request: Request,
    user: CurrentUser,
    session: Session,
    clock: CurrentClock,
    brain: Brain,
) -> dict[str, Any]:
    puzzle = await session.get(Puzzle, puzzle_id)
    if puzzle is None or puzzle.user_id != user.id:
        raise APIError("not_found", "問題が見つかりません", 404)
    if puzzle.submitted_at is not None:
        raise APIError("puzzle_already_submitted", "提出済みです", 409)
    if clock.now() >= puzzle.expires_at:
        raise APIError("puzzle_expired", "問題の期限が切れました", 409)
    week, now = await service.current(session, user.id), game_now(clock, user)
    if (
        week.id != puzzle.week_id
        or research_day(week.started_at, now) != puzzle.secret["research_day"]
        or (puzzle.kind == "meal" and slot_of(now) != puzzle.secret["slot"])
    ):
        raise APIError("puzzle_expired", "お世話の時間帯が変わりました", 409)
    state = await service.evaluate(session, week, now)
    await check_available(session, week, now, puzzle.kind)
    verified = MODULES[puzzle.kind].verify(puzzle.params, body)
    if verified.valid:
        # Training reports only elapsed time; other games report explicit action times.
        last_t = body.get("elapsed_ms", 0)
        if puzzle.kind == "meal":
            last_t = max((m["t"] for m in body["moves"]), default=0)
        elif puzzle.kind == "cleaning":
            last_t = body["taps"][-1]
        elif puzzle.kind == "temperature":
            last_t = body["stop_ms"]
        verified_time = verify_wall_clock(puzzle.issued_at, clock.now(), last_t)
        if not verified_time.valid:
            verified = verified_time
        elif puzzle.kind == "training":
            # A client can underreport elapsed_ms. Grade against at least the
            # server duration, just as the daily circuit does.
            elapsed_ms = max(
                body["elapsed_ms"], int((clock.now() - puzzle.issued_at).total_seconds() * 1000)
            )
            verified = training.verify(puzzle.params, body | {"elapsed_ms": elapsed_ms})
    if not verified.valid:
        raise APIError("invalid_submission", "操作記録が不正です", 422, {"reason": verified.reason})
    result = verified.to_dict()
    random = rng()
    if puzzle.kind == "meal":
        result |= meal.roll(
            random,
            verified.score,
            puzzle.secret["research_day"],
            (await service.team_bonus(session, user.id))["great_bonus"],
        )
        computed = stats.apply_meal(service.state_stats(state), result["great_success"])
        state.hunger, state.hunger_zero_since = computed.hunger, computed.hunger_zero_since
        state.growth += result["effects"]["growth"]
    elif puzzle.kind == "cleaning":
        state.cleanliness = stats.apply_cleaning(
            service.state_stats(state), verified.score
        ).cleanliness
        result["effects"] = {"cleanliness": verified.score}
    elif puzzle.kind == "training":
        result |= training.roll(random, verified.stars)
        cue, valence = puzzle.params["cue"], puzzle.params["valence"]
        if request.app.state.settings.brain_mode == "queue":
            result |= {"association": None, "skill_unlocked": None}
        else:
            learned, value = brain.train(
                brain_snapshot(state),
                cue,
                valence,
                result["learning_strength"],
                random.getrandbits(63),
            )
            store_brain(state, learned, brain)
            skill = training.skill_unlocked(cue, value)
            result |= {
                "association": {"cue": cue, "valence": valence, "value": value},
                "skill_unlocked": skill if skill and skill not in state.skills else None,
            }
            if skill:
                state.skills = state.skills | {skill: True}
    elif puzzle.kind == "pupation_site":
        result |= pupation_site.roll(random, puzzle.params, puzzle.secret, body)
    event = await record_care(session, user.id, week.id, week.started_at, now, puzzle.kind, result)
    result = result | {"seq": event.seq, "event_id": event.id}
    if puzzle.kind == "training" and request.app.state.settings.brain_mode == "queue":
        from tsuyulabo_api.services.training import prepare

        result = await prepare(
            session,
            request,
            user.id,
            event,
            puzzle,
            {
                "cue": cue,
                "valence": valence,
                "strength": result["learning_strength"],
                "seed": random.getrandbits(63),
            },
            result,
        )
    puzzle.submitted_at, puzzle.result = clock.now(), result
    await session.flush()
    return result
