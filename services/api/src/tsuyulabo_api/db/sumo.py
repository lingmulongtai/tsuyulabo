from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from tsuyulabo_api.db.base import Base, UTCDateTime, new_id


class SumoBout(Base):
    __tablename__ = "sumo_bouts"
    __table_args__ = (UniqueConstraint("user_id", "game_day", "daily_index"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    adult_id: Mapped[str] = mapped_column(ForeignKey("adults.id"))
    opponent_id: Mapped[str | None] = mapped_column(ForeignKey("adults.id"))
    opponent_name: Mapped[str] = mapped_column(String(80))
    game_day: Mapped[str] = mapped_column(String(10))
    daily_index: Mapped[int]
    won: Mapped[bool]
    reward: Mapped[int]
    replay: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime())
