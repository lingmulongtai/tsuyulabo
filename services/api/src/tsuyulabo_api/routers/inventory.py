from __future__ import annotations

from fastapi import APIRouter
from sqlalchemy import select
from tsuyulabo_api.db.models import Inventory
from tsuyulabo_api.services.game import CurrentUser, Session
from tsuyulabo_api.services.ledger import MATERIALS

router = APIRouter(prefix="/v1/inventory")


@router.get("")
async def inventory(user: CurrentUser, session: Session) -> dict[str, int]:
    rows = await session.scalars(select(Inventory).where(Inventory.user_id == user.id))
    return dict.fromkeys(MATERIALS, 0) | {row.material: row.amount for row in rows}
