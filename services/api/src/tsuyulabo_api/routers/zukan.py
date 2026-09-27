from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from sqlalchemy import select
from tsuyulabo_api.db.models import Adult
from tsuyulabo_api.domain.constants import STRAINS
from tsuyulabo_api.services.adults import expressed_phenotypes
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
    strains = {
        phenotype
        for adult in await session.scalars(select(Adult).where(Adult.user_id == user.id))
        for phenotype in expressed_phenotypes(adult)
    }
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
