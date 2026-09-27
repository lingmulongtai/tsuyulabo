from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from tsuyulabo_api.db.base import Base, UTCDateTime, new_id, utc_now


class Decoration(Base):
    __tablename__ = "decorations"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    item_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    source: Mapped[str] = mapped_column(String(20))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)


class DecorationLayout(Base):
    __tablename__ = "decoration_layouts"

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    layout: Mapped[dict[str, Any]] = mapped_column(JSON)


class ContestEntry(Base):
    __tablename__ = "contest_entries"
    __table_args__ = (UniqueConstraint("week", "user_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    week: Mapped[str] = mapped_column(String(8), index=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    adult_id: Mapped[str] = mapped_column(ForeignKey("adults.id"))
    layout: Mapped[dict[str, Any]] = mapped_column(JSON)
    entered_at: Mapped[datetime] = mapped_column(UTCDateTime())
    participation_paid: Mapped[bool] = mapped_column(default=False)
    placement_paid: Mapped[bool] = mapped_column(default=False)


class ContestVote(Base):
    __tablename__ = "contest_votes"
    __table_args__ = (UniqueConstraint("voter_id", "entry_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    week: Mapped[str] = mapped_column(String(8), index=True)
    voter_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    entry_id: Mapped[str] = mapped_column(ForeignKey("contest_entries.id"))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime())
