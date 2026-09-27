from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from sqlalchemy import select
from tsuyulabo_api.db.models import Adult
from tsuyulabo_api.domain.constants import STRAINS
from tsuyulabo_api.services.game import CurrentUser, Session

router = APIRouter(prefix="/v1/zukan")
BEHAVIORS = (
    "rest",
    "walk",
    "turn_left",
    "turn_right",
    "feed",
    "escape",
    "groom",
    "approach",
    "avoid",
)


@router.get("")
async def zukan(user: CurrentUser, session: Session) -> dict[str, Any]:
    strains = set(await session.scalars(select(Adult.strain).where(Adult.user_id == user.id)))
    observed = set(user.observed_behaviors) & set(BEHAVIORS)
    return {
        "behaviors": [{"id": label, "observed": label in observed} for label in BEHAVIORS],
        "strains": [
            {"id": strain, "name": name, "observed": strain in strains}
            for strain, name in STRAINS.items()
        ],
        "completion": {
            "behaviors": len(observed) / len(BEHAVIORS),
            "strains": len(strains & set(STRAINS)) / len(STRAINS),
        },
    }
