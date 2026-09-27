from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Literal

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict
from sqlalchemy import or_, select
from tsuyulabo_api.db.models import Adult, MatingProposal, PendingEgg, User
from tsuyulabo_api.domain import genetics
from tsuyulabo_api.errors import APIError
from tsuyulabo_api.routers.friends import lock_pair
from tsuyulabo_api.routers.users import CurrentUser
from tsuyulabo_api.services import mating as service
from tsuyulabo_api.services.adults import owned
from tsuyulabo_api.services.clock import game_now
from tsuyulabo_api.services.game import CurrentClock, Session, rng
from tsuyulabo_api.services.idempotency import IdempotentRoute

router = APIRouter(route_class=IdempotentRoute)


class ProposeMating(BaseModel):
    model_config = ConfigDict(extra="forbid")
    friend_id: str
    adult_id: str
    friend_adult_id: str


class MatingView(BaseModel):
    id: str
    proposer_id: str
    proposer_name: str
    recipient_id: str
    recipient_name: str
    mother_id: str
    mother_name: str
    father_id: str
    father_name: str
    status: Literal["pending", "accepted", "declined", "expired"]
    created_at: datetime
    expires_at: datetime


class MatingInbox(BaseModel):
    incoming: list[MatingView]
    outgoing: list[MatingView]


class MatingGenotype(BaseModel):
    sex: Literal["f", "m"]
    w: list[Literal["+", "w"]]
    y: list[Literal["+", "y"]]
    e: list[Literal["+", "e"]]
    vg: list[Literal["+", "vg"]]
    Cy: list[Literal["+", "Cy"]]


class MatingOption(BaseModel):
    id: str
    name: str
    sex: Literal["f", "m"]
    genotype: MatingGenotype
    available: bool


class PendingEggView(BaseModel):
    id: str
    proposal_id: str
    mother_id: str
    mother_name: str
    father_id: str
    father_name: str
    created_at: datetime


@router.get("/friend-mating/options/{friend_id}", response_model=list[MatingOption])
async def options(
    friend_id: str, user: CurrentUser, session: Session, clock: CurrentClock
) -> list[dict[str, Any]]:
    friend = await lock_pair(session, user.id, friend_id)
    now = max(game_now(clock, user), game_now(clock, friend))
    return [
        {
            "id": adult.id,
            "name": adult.name,
            "sex": adult.sex,
            "genotype": adult.genotype,
            "available": service.available(adult, now),
        }
        for adult in await session.scalars(select(Adult).where(Adult.user_id == friend_id))
    ]


@router.post("/friend-mating", status_code=201, response_model=MatingView)
async def propose(
    body: ProposeMating, user: CurrentUser, session: Session, clock: CurrentClock
) -> dict[str, Any]:
    friend = await lock_pair(session, user.id, body.friend_id)
    now = max(game_now(clock, user), game_now(clock, friend))
    own = await owned(session, user.id, body.adult_id)
    other = await owned(session, friend.id, body.friend_adult_id)
    if own.sex == other.sex:
        raise APIError("validation_error", "異なる性別の成虫を選んでください", 422)
    mother, father = (own, other) if own.sex == "f" else (other, own)
    service.require_available(mother, father, now=now)
    if await session.scalar(
        select(MatingProposal.id).where(
            MatingProposal.mother_id == mother.id,
            MatingProposal.father_id == father.id,
            MatingProposal.week_boundary == service.boundary(now),
        )
    ):
        raise APIError("proposal_already_sent", "このふたりのお見合いは今週申込済みです", 409)
    proposal = MatingProposal(
        proposer_id=user.id,
        recipient_id=friend.id,
        mother_id=mother.id,
        father_id=father.id,
        week_boundary=service.boundary(now),
        created_at=now,
        expires_at=now + timedelta(hours=48),
        status="pending",
    )
    session.add(proposal)
    await session.flush()
    service.notify(session, proposal, now)
    return await service.payload(session, proposal, now)


@router.get("/friend-mating", response_model=MatingInbox)
async def inbox(user: CurrentUser, session: Session, clock: CurrentClock) -> dict[str, Any]:
    result: dict[str, list[dict[str, Any]]] = {"incoming": [], "outgoing": []}
    proposals = await session.scalars(
        select(MatingProposal)
        .where(or_(MatingProposal.proposer_id == user.id, MatingProposal.recipient_id == user.id))
        .order_by(MatingProposal.created_at.desc(), MatingProposal.id)
    )
    for proposal in proposals:
        other_id = (
            proposal.recipient_id if proposal.proposer_id == user.id else proposal.proposer_id
        )
        other = await session.get(User, other_id)
        now = max(game_now(clock, user), game_now(clock, other))
        direction = "outgoing" if proposal.proposer_id == user.id else "incoming"
        result[direction].append(await service.payload(session, proposal, now))
    return result


async def respond(
    proposal_id: str, user: User, session: Session, clock: CurrentClock, *, accept: bool
) -> dict[str, Any]:
    proposal = await session.get(MatingProposal, proposal_id)
    if proposal is None or proposal.recipient_id != user.id:
        raise APIError("not_found", "お見合いが見つかりません", 404)
    other = await lock_pair(session, user.id, proposal.proposer_id, require_friend=accept)
    # Reload after waiting on the pair locks; a competing response may have completed.
    await session.refresh(proposal)
    now = max(game_now(clock, user), game_now(clock, other))
    if service.status(proposal, now) != "pending":
        raise APIError("proposal_unavailable", "このお見合いは終了しています", 409)
    if accept:
        mother = await session.get(Adult, proposal.mother_id)
        father = await session.get(Adult, proposal.father_id)
        if {mother.user_id, father.user_id} != {user.id, other.id}:
            raise APIError("not_found", "親が見つかりません", 404)
        if mother.sex != "f" or father.sex != "m":
            raise APIError("validation_error", "親の性別が不正です", 422)
        service.require_available(mother, father, now=now)
        random = rng()
        for owner in (proposal.proposer_id, proposal.recipient_id):
            child = genetics.breed(random, mother.genotype, father.genotype)
            session.add(
                PendingEgg(
                    proposal_id=proposal.id,
                    user_id=owner,
                    genotype=child.genotype,
                    lethal_redraws=child.lethal_redraws,
                    created_at=now,
                )
            )
        mother.last_parent_week = father.last_parent_week = service.boundary(now)
    proposal.status = "accepted" if accept else "declined"
    service.notify(session, proposal, now)
    await session.flush()
    return await service.payload(session, proposal, now)


@router.post("/friend-mating/{proposal_id}/accept", response_model=MatingView)
async def accept(
    proposal_id: str, user: CurrentUser, session: Session, clock: CurrentClock
) -> dict[str, Any]:
    return await respond(proposal_id, user, session, clock, accept=True)


@router.post("/friend-mating/{proposal_id}/decline", response_model=MatingView)
async def decline(
    proposal_id: str, user: CurrentUser, session: Session, clock: CurrentClock
) -> dict[str, Any]:
    return await respond(proposal_id, user, session, clock, accept=False)


@router.get("/pending-eggs", response_model=list[PendingEggView])
async def pending(user: CurrentUser, session: Session) -> list[dict[str, Any]]:
    return await service.pending_payloads(session, user.id)
