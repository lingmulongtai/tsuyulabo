from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, CheckConstraint, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from tsuyulabo_api.db.base import Base, UTCDateTime, new_id, utc_now


class Inventory(Base):
    __tablename__ = "inventory"
    __table_args__ = (CheckConstraint("amount >= 0", name="nonnegative_amount"),)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    material: Mapped[str] = mapped_column(String(40), primary_key=True)
    amount: Mapped[int] = mapped_column(BigInteger, default=0)


class LedgerAccount(Base):
    __tablename__ = "ledger_accounts"
    __table_args__ = (
        UniqueConstraint("owner", "currency"),
        CheckConstraint("currency IN ('shizuku', 'research_points', 'kohaku')", name="currency"),
        CheckConstraint("balance >= 0 OR owner LIKE 'system:%'", name="user_balance"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner: Mapped[str] = mapped_column(String(100))
    currency: Mapped[str] = mapped_column(String(24))
    balance: Mapped[int] = mapped_column(BigInteger, default=0)


class LedgerEntry(Base):
    __tablename__ = "ledger_entries"
    __table_args__ = (UniqueConstraint("tx_id", "account_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    tx_id: Mapped[str] = mapped_column(String(36), index=True)
    account_id: Mapped[str] = mapped_column(ForeignKey("ledger_accounts.id"), index=True)
    amount: Mapped[int] = mapped_column(BigInteger)
    reason: Mapped[str] = mapped_column(String(100))
    ref: Mapped[str | None] = mapped_column(String(200))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    # Guest registration uses a reserved anonymous scope before a user exists.
    user_id: Mapped[str] = mapped_column(String(36), primary_key=True)
    key: Mapped[str] = mapped_column(String(36), primary_key=True)
    method: Mapped[str] = mapped_column(String(10))
    path: Mapped[str] = mapped_column(String(500))
    status_code: Mapped[int | None]
    response: Mapped[dict[str, Any] | list[Any] | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now, index=True)
