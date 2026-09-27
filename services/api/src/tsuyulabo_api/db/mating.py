from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from tsuyulabo_api.db.base import Base, UTCDateTime, new_id


class MatingProposal(Base):
    __tablename__ = "mating_proposals"
    __table_args__ = (
        UniqueConstraint("mother_id", "father_id", "week_boundary"),
        CheckConstraint("proposer_id <> recipient_id", name="different_players"),
        CheckConstraint("status IN ('pending', 'accepted', 'declined')", name="status"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    proposer_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    recipient_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    mother_id: Mapped[str] = mapped_column(ForeignKey("adults.id"))
    father_id: Mapped[str] = mapped_column(ForeignKey("adults.id"))
    week_boundary: Mapped[datetime] = mapped_column(UTCDateTime())
    created_at: Mapped[datetime] = mapped_column(UTCDateTime())
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime())
    status: Mapped[str] = mapped_column(String(16), default="pending")


class PendingEgg(Base):
    __tablename__ = "pending_eggs"
    __table_args__ = (
        UniqueConstraint("proposal_id", "user_id"),
        CheckConstraint("lethal_redraws >= 0", name="redraws_nonnegative"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    proposal_id: Mapped[str] = mapped_column(ForeignKey("mating_proposals.id"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    genotype: Mapped[dict[str, Any]] = mapped_column(JSON)
    lethal_redraws: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(UTCDateTime())
    consumed_week_id: Mapped[str | None] = mapped_column(ForeignKey("weeks.id"), unique=True)
