"""Individual diary history and durable quiet-hint cooldowns."""

from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, Date, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from tsuyulabo_api.db.base import Base, UTCDateTime, new_id, utc_now


class DiaryEntry(Base):
    __tablename__ = "diary_entries"
    __table_args__ = (UniqueConstraint("user_id", "week_id", "day"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    week_id: Mapped[str] = mapped_column(ForeignKey("weeks.id"), index=True)
    day: Mapped[date] = mapped_column(Date)
    text: Mapped[str]
    evidence: Mapped[list[str]] = mapped_column(JSON)
    snapshot: Mapped[dict[str, Any]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)


class QuietHint(Base):
    __tablename__ = "quiet_hints"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    week_id: Mapped[str] = mapped_column(ForeignKey("weeks.id"), index=True)
    kind: Mapped[str] = mapped_column(String(16))
    text: Mapped[str]
    evidence: Mapped[list[str]] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)
    dismissed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
