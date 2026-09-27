from __future__ import annotations

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import or_, select
from tsuyulabo_api.db.models import Adult, Friendship, Job, MazeEntry, MazeRace, MazeSlot, User
from tsuyulabo_api.db.operations import insert_if_absent
from tsuyulabo_api.domain import maze
from tsuyulabo_api.errors import APIError
from tsuyulabo_api.services.brain_state import snapshot
from tsuyulabo_api.services.dispatch import enqueue
from tsuyulabo_api.services.game import CurrentClock, CurrentUser, Session
from tsuyulabo_api.services.idempotency import IdempotentRoute

router = APIRouter(prefix="/v1/races", route_class=IdempotentRoute)
Cue = Literal["banana", "apple_vinegar", "yeast", "grape", "blue_light"]


class MazeToken(BaseModel):
    model_config = ConfigDict(extra="forbid")
    x: int = Field(ge=0, le=8, strict=True)
    y: int = Field(ge=0, le=8, strict=True)
    cue: Cue


class MazeGeometry(BaseModel):
    grid: list[str]
    start: list[int] = Field(min_length=2, max_length=2)
    goal: list[int] = Field(min_length=2, max_length=2)


class MazeFrame(BaseModel):
    x: int
    y: int
    heading: int


class MazeResult(BaseModel):
    reached: bool
    steps: int
    distance_left: int
    frames: list[MazeFrame]


class RaceEntryView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    adult_id: str
    job_id: str
    placements: list[MazeToken]
    submitted_at: datetime
    status: str


class CurrentRace(BaseModel):
    week: str
    maze: MazeGeometry
    deadline: datetime
    my_entry: RaceEntryView | None


class EnterRace(BaseModel):
    model_config = ConfigDict(extra="forbid")
    week: str = Field(pattern=r"^\d{4}-W\d{2}$")
    adult_id: str
    placements: list[MazeToken] = Field(max_length=3)


class RaceReplay(BaseModel):
    week: str
    maze: MazeGeometry
    entry: RaceEntryView
    result: MazeResult | None


class RaceRank(BaseModel):
    rank: int
    entry_id: str
    user_id: str
    display_name: str
    is_me: bool
    reached: bool
    steps: int
    distance_left: int


class RaceRanking(BaseModel):
    week: str
    entries: list[RaceRank]


async def current_race(session: Session, now: datetime) -> MazeRace:
    week, deadline = maze.week_at(now)
    await insert_if_absent(
        session,
        MazeRace,
        {"week": week, "deadline": deadline, "maze": maze.generate(week)},
        ["week"],
    )
    return await session.get(MazeRace, week)


async def entry_view(session: Session, entry: MazeEntry) -> RaceEntryView:
    job = await session.get(Job, entry.job_id)
    return RaceEntryView(
        id=entry.id,
        adult_id=entry.adult_id,
        job_id=entry.job_id,
        placements=entry.placements,
        submitted_at=entry.submitted_at,
        status=job.status,
    )


@router.get("/current")
async def current(user: CurrentUser, session: Session, clock: CurrentClock) -> CurrentRace:
    race = await current_race(session, clock.now())
    slot = await session.get(MazeSlot, (user.id, race.week))
    entry = await session.get(MazeEntry, slot.entry_id) if slot else None
    return CurrentRace(
        week=race.week,
        maze=race.maze,
        deadline=race.deadline,
        my_entry=await entry_view(session, entry) if entry else None,
    )


@router.post("/current/entry")
async def enter(
    body: EnterRace,
    request: Request,
    tasks: BackgroundTasks,
    user: CurrentUser,
    session: Session,
    clock: CurrentClock,
) -> RaceEntryView:
    now = clock.now()
    race = await current_race(session, now)
    if body.week != race.week:
        raise APIError("race_expired", "新しい週の迷路に切り替わりました", 409)
    adult = await session.scalar(
        select(Adult).where(
            Adult.id == body.adult_id,
            Adult.user_id == user.id,
        )
    )
    if adult is None:
        raise APIError("not_found", "成虫が見つかりません", 404)
    cells = {(token.x, token.y) for token in body.placements}
    if len(cells) != len(body.placements) or any(
        not maze.is_open(race.maze, x, y) for x, y in cells
    ):
        raise APIError("invalid_submission", "合図は別々の通路に置いてください", 422)
    placements = [token.model_dump() for token in body.placements]
    job = await enqueue(
        session,
        request,
        tasks,
        user.id,
        "brain.maze_run",
        {
            "maze": race.maze,
            "placements": placements,
            "snapshot": snapshot(adult),
            "seed": maze.seed_for(race.week, user.id),
        },
    )
    entry = MazeEntry(
        week=race.week,
        user_id=user.id,
        adult_id=adult.id,
        job_id=job.id,
        placements=placements,
        submitted_at=now,
    )
    session.add(entry)
    await session.flush()
    slot = await session.get(MazeSlot, (user.id, race.week))
    if slot:
        slot.entry_id = entry.id
    else:
        session.add(MazeSlot(user_id=user.id, week=race.week, entry_id=entry.id))
    await session.flush()
    return await entry_view(session, entry)


@router.get("/current/ranking")
async def ranking(user: CurrentUser, session: Session, clock: CurrentClock) -> RaceRanking:
    week, _ = maze.week_at(clock.now())
    friends = select(Friendship.friend_id).where(Friendship.user_id == user.id)
    rows = (
        await session.execute(
            select(MazeEntry, Job, User)
            .join(MazeSlot, MazeSlot.entry_id == MazeEntry.id)
            .join(Job, Job.id == MazeEntry.job_id)
            .join(User, User.id == MazeEntry.user_id)
            .where(
                MazeSlot.week == week,
                Job.status == "succeeded",
                or_(User.id == user.id, User.id.in_(friends)),
            )
        )
    ).all()

    def score(row: tuple) -> tuple[int, int]:
        result = row[1].result
        return (0, result["steps"]) if result["reached"] else (1, result["distance_left"])

    rows = sorted(rows, key=lambda row: (*score(row), row[2].id))
    entries = []
    previous = None
    rank = 0
    for index, row in enumerate(rows, 1):
        entry, job, person = row
        if score(row) != previous:
            rank, previous = index, score(row)
        entries.append(
            RaceRank(
                rank=rank,
                entry_id=entry.id,
                user_id=person.id,
                display_name=person.display_name,
                is_me=person.id == user.id,
                **{key: job.result[key] for key in ("reached", "steps", "distance_left")},
            )
        )
    return RaceRanking(week=week, entries=entries)


@router.get("/entries/{entry_id}/replay")
async def replay(entry_id: str, user: CurrentUser, session: Session) -> RaceReplay:
    entry = await session.get(MazeEntry, entry_id)
    if entry is None or (
        entry.user_id != user.id and not await session.get(Friendship, (user.id, entry.user_id))
    ):
        raise APIError("not_found", "レースが見つかりません", 404)
    race = await session.get(MazeRace, entry.week)
    job = await session.get(Job, entry.job_id)
    return RaceReplay(
        week=entry.week,
        maze=race.maze,
        entry=await entry_view(session, entry),
        result=job.result if job.status == "succeeded" else None,
    )
