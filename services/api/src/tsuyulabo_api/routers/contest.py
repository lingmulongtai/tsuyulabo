from __future__ import annotations

from datetime import timedelta
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select, update
from tsuyulabo_api.db.models import (
    Adult,
    ContestEntry,
    ContestVote,
    Decoration,
    DecorationLayout,
    Friendship,
    LedgerAccount,
    LedgerEntry,
    User,
    Week,
)
from tsuyulabo_api.domain import contest
from tsuyulabo_api.errors import APIError
from tsuyulabo_api.services.game import CurrentClock, CurrentUser, Session, reward
from tsuyulabo_api.services.idempotency import IdempotentRoute

decorations_router = APIRouter(prefix="/v1/decorations", route_class=IdempotentRoute)
router = APIRouter(prefix="/v1/contest", route_class=IdempotentRoute)
EMPTY_LAYOUT: dict[str, str | None] = dict.fromkeys(contest.SLOTS)


class LayoutBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    vial: str | None = None
    background: str | None = None
    left: str | None = None
    right: str | None = None
    accessory: str | None = None


class EntryBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    adult_id: str


class VoteBody(BaseModel):
    model_config = ConfigDict(extra="forbid")
    entry_id: str


async def grant_earned(session: Session, user_id: str) -> None:
    ranks = set(
        await session.scalars(
            select(Week.rank).where(Week.user_id == user_id, Week.status == "eclosed")
        )
    )
    points = (
        await session.scalar(
            select(func.coalesce(func.sum(LedgerEntry.amount), 0))
            .join(LedgerAccount, LedgerAccount.id == LedgerEntry.account_id)
            .where(
                LedgerAccount.owner == f"user:{user_id}",
                LedgerAccount.currency == "research_points",
                LedgerEntry.amount > 0,
            )
        )
        or 0
    )
    research_rank = min(99, 1 + points // 100)
    owned = set(
        await session.scalars(select(Decoration.item_id).where(Decoration.user_id == user_id))
    )
    highest = max((contest.RANKS.get(rank or "normal", 0) for rank in ranks), default=0)
    for item_id, (_, _, source, threshold) in contest.ITEMS.items():
        earned = (
            source == "starter"
            or (source == "presentation" and highest >= contest.RANKS[str(threshold)])
            or (source == "research" and research_rank >= int(threshold))
        )
        if earned and item_id not in owned:
            session.add(Decoration(user_id=user_id, item_id=item_id, source=source))
    await session.flush()


async def checked_layout(
    session: Session, user_id: str, layout: dict[str, str | None], *, contest_entry: bool = False
) -> None:
    if not contest.valid_layout(layout):
        raise APIError("invalid_layout", "装飾の配置が正しくありません", 422)
    await grant_earned(session, user_id)
    owned = {
        row.item_id: row.source
        for row in await session.scalars(select(Decoration).where(Decoration.user_id == user_id))
    }
    if any(
        item not in owned or (contest_entry and owned[item] == "paid")
        for item in layout.values()
        if item
    ):
        raise APIError("decoration_unavailable", "使えない装飾が含まれています", 422)


@decorations_router.get("")
async def inventory(user: CurrentUser, session: Session) -> dict[str, Any]:
    await grant_earned(session, user.id)
    owned = list(await session.scalars(select(Decoration).where(Decoration.user_id == user.id)))
    saved = await session.get(DecorationLayout, user.id)
    return {
        "catalog": [
            {"id": key, "kind": value[0], "name": value[1]} for key, value in contest.ITEMS.items()
        ],
        "owned": [{"id": row.item_id, "source": row.source} for row in owned],
        "layout": saved.layout if saved else EMPTY_LAYOUT,
    }


@decorations_router.put("/layout")
async def equip(body: LayoutBody, user: CurrentUser, session: Session) -> dict[str, str | None]:
    layout = body.model_dump()
    await checked_layout(session, user.id, layout)
    saved = await session.get(DecorationLayout, user.id)
    if saved:
        saved.layout = layout
    else:
        session.add(DecorationLayout(user_id=user.id, layout=layout))
    return layout


async def entry_dict(
    session: Session, entry: ContestEntry, viewer: str, votes_visible: bool
) -> dict[str, Any]:
    person = await session.get(User, entry.user_id)
    adult = await session.get(Adult, entry.adult_id)
    votes = await session.scalar(
        select(func.count()).select_from(ContestVote).where(ContestVote.entry_id == entry.id)
    )
    return {
        "id": entry.id,
        "user_id": entry.user_id,
        "display_name": person.display_name,
        "adult_name": adult.name,
        "adult_id": adult.id,
        "strain": adult.strain,
        "sex": adult.sex,
        "layout": entry.layout,
        "entered_at": entry.entered_at,
        "is_me": entry.user_id == viewer,
        "votes": votes if votes_visible else None,
    }


@router.get("/current")
async def current(user: CurrentUser, session: Session, clock: CurrentClock) -> dict[str, Any]:
    now = clock.now()
    week, entry_close, vote_close, theme = contest.week_at(now)
    friends = select(Friendship.friend_id).where(Friendship.user_id == user.id)
    entries = list(
        await session.scalars(
            select(ContestEntry).where(ContestEntry.week == week, ContestEntry.user_id.in_(friends))
        )
    )
    mine = await session.scalar(
        select(ContestEntry).where(ContestEntry.week == week, ContestEntry.user_id == user.id)
    )
    used = (
        await session.scalar(
            select(func.count())
            .select_from(ContestVote)
            .where(ContestVote.week == week, ContestVote.voter_id == user.id)
        )
        or 0
    )
    voted = list(
        await session.scalars(
            select(ContestVote.entry_id).where(
                ContestVote.week == week, ContestVote.voter_id == user.id
            )
        )
    )
    return {
        "week": week,
        "theme": theme,
        "phase": contest.phase(now, entry_close, vote_close),
        "entry_close": entry_close,
        "vote_close": vote_close,
        "votes_left": max(0, 3 - used),
        "voted_entry_ids": voted,
        "my_entry": await entry_dict(session, mine, user.id, False) if mine else None,
        "friends": [await entry_dict(session, entry, user.id, False) for entry in entries],
    }


@router.post("/current/entry")
async def enter(
    body: EntryBody, user: CurrentUser, session: Session, clock: CurrentClock
) -> dict[str, Any]:
    now = clock.now()
    week, close, _, _ = contest.week_at(now)
    if now >= close:
        raise APIError("entries_closed", "応募期間は終了しました", 409)
    if await session.scalar(
        select(ContestEntry.id).where(ContestEntry.week == week, ContestEntry.user_id == user.id)
    ):
        raise APIError("already_entered", "今週は応募済みです", 409)
    adult = await session.scalar(
        select(Adult).where(Adult.id == body.adult_id, Adult.user_id == user.id)
    )
    if adult is None:
        raise APIError("not_found", "成虫が見つかりません", 404)
    saved = await session.get(DecorationLayout, user.id)
    layout = saved.layout.copy() if saved else EMPTY_LAYOUT.copy()
    await checked_layout(session, user.id, layout, contest_entry=True)
    entry = ContestEntry(
        week=week,
        user_id=user.id,
        adult_id=adult.id,
        layout=layout,
        entered_at=now,
        participation_paid=True,
        placement_paid=False,
    )
    session.add(entry)
    await session.flush()
    await reward(session, user.id, "shizuku", 5, "contest_participation", entry.id)
    return await entry_dict(session, entry, user.id, False)


@router.post("/current/votes")
async def vote(
    body: VoteBody, user: CurrentUser, session: Session, clock: CurrentClock
) -> dict[str, int]:
    now = clock.now()
    week, close, vote_close, _ = contest.week_at(now)
    if not close <= now < vote_close:
        raise APIError("voting_closed", "投票期間外です", 409)
    entry = await session.get(ContestEntry, body.entry_id)
    if (
        entry is None
        or entry.week != week
        or entry.user_id == user.id
        or not await session.get(Friendship, (user.id, entry.user_id))
    ):
        raise APIError("not_found", "投票できる応募が見つかりません", 404)
    used = (
        await session.scalar(
            select(func.count())
            .select_from(ContestVote)
            .where(ContestVote.week == week, ContestVote.voter_id == user.id)
        )
        or 0
    )
    if used >= 3 or await session.scalar(
        select(ContestVote.id).where(
            ContestVote.voter_id == user.id, ContestVote.entry_id == entry.id
        )
    ):
        raise APIError("vote_limit", "この応募には投票できません", 409)
    session.add(ContestVote(week=week, voter_id=user.id, entry_id=entry.id, created_at=now))
    return {"votes_left": 2 - used}


@router.get("/results")
async def results(user: CurrentUser, session: Session, clock: CurrentClock) -> dict[str, Any]:
    now = clock.now()
    week, _, close, _ = contest.week_at(now)
    if now < close:
        week = contest.week_at(now - timedelta(days=7))[0]
    entries = list(await session.scalars(select(ContestEntry).where(ContestEntry.week == week)))
    counts = {
        entry.id: (
            await session.scalar(
                select(func.count())
                .select_from(ContestVote)
                .where(ContestVote.entry_id == entry.id)
            )
            or 0
        )
        for entry in entries
    }
    ordered = contest.rank_entries(
        [(entry.id, counts[entry.id], entry.entered_at) for entry in entries]
    )
    by_id = {entry.id: entry for entry in entries}
    for rank, entry_id in enumerate(ordered[:3], 1):
        entry = by_id[entry_id]
        claimed = await session.execute(
            update(ContestEntry)
            .where(ContestEntry.id == entry.id, ContestEntry.placement_paid.is_(False))
            .values(placement_paid=True)
        )
        if claimed.rowcount:
            await reward(
                session,
                entry.user_id,
                "shizuku",
                {1: 30, 2: 20, 3: 10}[rank],
                "contest_placement",
                entry.id,
            )
    return {
        "week": week,
        "entries": [
            dict(await entry_dict(session, by_id[entry_id], user.id, True), rank=rank)
            for rank, entry_id in enumerate(ordered, 1)
        ],
    }
