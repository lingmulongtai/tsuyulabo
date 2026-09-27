from __future__ import annotations

from collections import Counter
from datetime import datetime
from math import floor
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tsuyulabo_api.brain_adapter import BrainAdapter
from tsuyulabo_api.db.models import Adult, TeamSlot
from tsuyulabo_api.domain import adults, team
from tsuyulabo_api.errors import APIError
from tsuyulabo_api.services import adults as adult_service
from tsuyulabo_api.services.game import reward, rng
from tsuyulabo_api.services.ledger import add_material


def tuples(value: Any) -> Any:
    return tuple(tuples(item) for item in value) if isinstance(value, list) else value


async def settle(
    session: AsyncSession, user_id: str, now: datetime, brain: BrainAdapter
) -> list[tuple[TeamSlot, Adult]]:
    members = list(
        (
            await session.execute(
                select(TeamSlot, Adult)
                .join(Adult, TeamSlot.adult_id == Adult.id)
                .where(TeamSlot.user_id == user_id)
                .order_by(TeamSlot.slot)
            )
        ).all()
    )
    for slot, adult in members:
        if now < slot.last_computed_at:
            raise APIError("time_reversed", "時刻を前回の計算時刻以降に進めてください", 409)
        adult_service.payload(adult, brain)
        random = rng()
        bag = slot.bag
        if "rng" in bag:
            random.setstate(tuples(bag["rng"]))
        state = team.GatherState(
            slot.last_computed_at,
            adult.level,
            adult.energy,
            tuple(bag.get("items", [])),
            bag.get("item_progress", 0),
            bag.get("shizuku", 0),
            bag.get("pending_exp", 0),
        )
        result = team.gather(state, now, random, adult.preferences, adult.subskills)
        slot.bag = {
            "items": list(result.bag),
            "item_progress": result.item_progress,
            "shizuku": result.shizuku,
            "pending_exp": result.pending_exp,
            "rng": random.getstate(),
        }
        slot.last_computed_at, adult.energy = now, result.energy
    await session.flush()
    return members


def payload(members: list[tuple[TeamSlot, Adult]]) -> dict[str, Any]:
    count = sum(len(slot.bag.get("items", [])) for slot, _ in members)
    return {
        "members": [
            adult_service.payload(adult)
            | {
                "slot": slot.slot,
                "bag": dict(Counter(slot.bag.get("items", []))),
                "shizuku": floor(slot.bag.get("shizuku", 0)),
                "pending_exp": slot.bag.get("pending_exp", 0),
            }
            for slot, adult in members
        ],
        "bag_total": count,
        "collectable": count > 0 or any(slot.bag.get("shizuku", 0) >= 1 for slot, _ in members),
    }


async def collect(
    session: AsyncSession, user_id: str, members: list[tuple[TeamSlot, Adult]]
) -> dict[str, Any]:
    materials: Counter[str] = Counter()
    shizuku = 0
    experience = {}
    for slot, adult in members:
        materials.update(slot.bag.get("items", []))
        drops = floor(slot.bag.get("shizuku", 0))
        shizuku += drops
        exp = slot.bag.get("pending_exp", 0)
        experience[adult.id] = exp
        adult_service.apply_progress(
            adult, adults.add_exp(adult_service.progress(adult), exp, rng())
        )
        slot.bag = slot.bag | {
            "items": [],
            "shizuku": slot.bag.get("shizuku", 0) - drops,
            "pending_exp": 0,
        }
    for material, amount in materials.items():
        await add_material(session, user_id, material, amount)
    await reward(session, user_id, "shizuku", shizuku, "gathering", user_id)
    return {"materials": dict(materials), "shizuku": shizuku, "exp": experience}
