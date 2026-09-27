from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tsuyulabo_api.brain_adapter import BrainAdapter
from tsuyulabo_api.db.models import Adult
from tsuyulabo_api.domain import adults as rules
from tsuyulabo_api.domain.constants import SUBSKILL_LEVELS
from tsuyulabo_api.errors import APIError


async def owned(session: AsyncSession, user_id: str, adult_id: str) -> Adult:
    adult = await session.scalar(
        select(Adult).where(Adult.id == adult_id, Adult.user_id == user_id)
    )
    if adult is None:
        raise APIError("not_found", "成虫が見つかりません", 404)
    return adult


def progress(adult: Adult) -> rules.AdultProgress:
    return rules.AdultProgress(
        adult.stars,
        adult.level,
        adult.exp,
        tuple(zip(SUBSKILL_LEVELS, adult.subskills, strict=False)),
    )


def apply_progress(adult: Adult, state: rules.AdultProgress) -> None:
    adult.level, adult.exp = state.level, state.exp
    adult.subskills = [skill for _, skill in state.subskills]


def payload(adult: Adult, brain: BrainAdapter | None = None) -> dict[str, Any]:
    return {
        "id": adult.id,
        "week_id": adult.week_id,
        "name": adult.name,
        "sex": adult.sex,
        "strain": adult.strain,
        "stars": adult.stars,
        "traits": adult.traits,
        "subskills": adult.subskills,
        "skills": adult.skills,
        "level": adult.level,
        "level_cap": rules.level_cap(adult.stars),
        "exp": adult.exp,
        "energy": round(adult.energy),
        "preferences": adult.preferences,
        "created_at": adult.created_at,
    }
