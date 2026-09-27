from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from tsuyulabo_api.db.base import Base, UTCDateTime, new_id


class MazeRace(Base):
    __tablename__ = "maze_races"

    week: Mapped[str] = mapped_column(String(8), primary_key=True)
    maze: Mapped[dict[str, Any]] = mapped_column(JSON)
    deadline: Mapped[datetime] = mapped_column(UTCDateTime())


class MazeEntry(Base):
    __tablename__ = "maze_entries"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    week: Mapped[str] = mapped_column(ForeignKey("maze_races.week"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    adult_id: Mapped[str] = mapped_column(ForeignKey("adults.id"))
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"))
    placements: Mapped[list[dict[str, Any]]] = mapped_column(JSON)
    submitted_at: Mapped[datetime] = mapped_column(UTCDateTime())


class MazeSlot(Base):
    __tablename__ = "maze_slots"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    week: Mapped[str] = mapped_column(ForeignKey("maze_races.week"), primary_key=True)
    entry_id: Mapped[str] = mapped_column(ForeignKey("maze_entries.id"))
