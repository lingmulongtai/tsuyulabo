from __future__ import annotations

from datetime import date, datetime
from typing import Any

from sqlalchemy import JSON, CheckConstraint, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from tsuyulabo_api.db.base import Base, UTCDateTime, new_id, utc_now


class Friendship(Base):
    __tablename__ = "friendships"
    __table_args__ = (CheckConstraint("user_id <> friend_id", name="different_users"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    friend_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)


class Like(Base):
    __tablename__ = "likes"

    from_user_id: Mapped[str] = mapped_column("from", ForeignKey("users.id"), primary_key=True)
    to_user_id: Mapped[str] = mapped_column("to", ForeignKey("users.id"), primary_key=True)
    day: Mapped[date] = mapped_column(primary_key=True)


class Gift(Base):
    __tablename__ = "gifts"
    __table_args__ = (CheckConstraint("amount BETWEEN 1 AND 5", name="amount_range"),)

    from_user_id: Mapped[str] = mapped_column("from", ForeignKey("users.id"), primary_key=True)
    to_user_id: Mapped[str] = mapped_column("to", ForeignKey("users.id"))
    material: Mapped[str] = mapped_column(String(40))
    amount: Mapped[int]
    day: Mapped[date] = mapped_column(primary_key=True)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    kind: Mapped[str] = mapped_column(String(40))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)
    read_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
