from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tsuyulabo_api.db.models import Adult, MatingProposal, Notification, PendingEgg, User
from tsuyulabo_api.domain.clock import day_start, game_day
from tsuyulabo_api.errors import APIError


def boundary(now: datetime) -> datetime:
    day = game_day(now)
    return day_start(day - timedelta(days=day.weekday()))


def available(adult: Adult, now: datetime) -> bool:
    return adult.last_parent_week is None or adult.last_parent_week < boundary(now)


def require_available(*adults: Adult, now: datetime) -> None:
    if not all(available(adult, now) for adult in adults):
        raise APIError("parent_already_used", "この親は今週すでに交配しています", 409)


def status(proposal: MatingProposal, now: datetime) -> str:
    if proposal.status == "pending" and now >= proposal.expires_at:
        return "expired"
    return proposal.status


async def payload(session: AsyncSession, proposal: MatingProposal, now: datetime) -> dict[str, Any]:
    proposer = await session.get(User, proposal.proposer_id)
    recipient = await session.get(User, proposal.recipient_id)
    mother = await session.get(Adult, proposal.mother_id)
    father = await session.get(Adult, proposal.father_id)
    return {
        "id": proposal.id,
        "proposer_id": proposer.id,
        "proposer_name": proposer.display_name,
        "recipient_id": recipient.id,
        "recipient_name": recipient.display_name,
        "mother_id": mother.id,
        "mother_name": mother.name,
        "father_id": father.id,
        "father_name": father.name,
        "status": status(proposal, now),
        "created_at": proposal.created_at,
        "expires_at": proposal.expires_at,
    }


def notify(session: AsyncSession, proposal: MatingProposal, now: datetime) -> None:
    for owner in (proposal.proposer_id, proposal.recipient_id):
        session.add(
            Notification(
                user_id=owner,
                kind=f"mating_{proposal.status}",
                payload={"proposal_id": proposal.id},
                created_at=now,
            )
        )


async def pending_payloads(session: AsyncSession, user_id: str) -> list[dict[str, Any]]:
    eggs = await session.scalars(
        select(PendingEgg)
        .where(PendingEgg.user_id == user_id, PendingEgg.consumed_week_id.is_(None))
        .order_by(PendingEgg.created_at, PendingEgg.id)
    )
    result = []
    for egg in eggs:
        proposal = await session.get(MatingProposal, egg.proposal_id)
        mother = await session.get(Adult, proposal.mother_id)
        father = await session.get(Adult, proposal.father_id)
        result.append(
            {
                "id": egg.id,
                "proposal_id": proposal.id,
                "mother_id": mother.id,
                "mother_name": mother.name,
                "father_id": father.id,
                "father_name": father.name,
                "created_at": egg.created_at,
            }
        )
    return result
