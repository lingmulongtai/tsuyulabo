from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import CheckConstraint, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from tsuyulabo_api.db.base import Base, UTCDateTime


class DailyCircuitAttempt(Base):
    __tablename__ = "daily_circuit_attempts"
    __table_args__ = (
        CheckConstraint("elapsed_ms >= 0", name="nonnegative_time"),
        Index("ix_daily_circuit_ranking", "day", "elapsed_ms", "submitted_at"),
    )

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    day: Mapped[date] = mapped_column(primary_key=True)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime())
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime())
    submitted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    elapsed_ms: Mapped[int | None]
    shizuku: Mapped[int | None]
