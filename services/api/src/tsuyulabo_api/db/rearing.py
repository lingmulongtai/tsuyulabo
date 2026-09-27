from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, CheckConstraint, ForeignKey, LargeBinary, String, UniqueConstraint
from sqlalchemy.engine.default import DefaultExecutionContext
from sqlalchemy.orm import Mapped, mapped_column
from tsuyulabo_api.db.base import Base, UTCDateTime, new_id, utc_now
from tsuyulabo_api.domain.genetics import wild_type


def default_genotype(context: DefaultExecutionContext) -> dict[str, Any]:
    return wild_type(context.get_current_parameters()["sex"])


class Week(Base):
    __tablename__ = "weeks"
    __table_args__ = (CheckConstraint("status IN ('active', 'eclosed')", name="status"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)
    status: Mapped[str] = mapped_column(String(16), default="active")
    rank: Mapped[str | None] = mapped_column(String(16))
    points: Mapped[int] = mapped_column(default=0)
    care_miss: Mapped[int] = mapped_column(default=0)
    eclosed_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    egg_genotype: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    mother_id: Mapped[str | None] = mapped_column(String(36))
    father_id: Mapped[str | None] = mapped_column(String(36))
    lethal_redraws: Mapped[int] = mapped_column(default=0, server_default="0")
    adult_id: Mapped[str | None] = mapped_column(
        ForeignKey("adults.id", use_alter=True, name="fk_weeks_adult_id_adults")
    )


class LarvaState(Base):
    __tablename__ = "larva_states"

    week_id: Mapped[str] = mapped_column(ForeignKey("weeks.id"), primary_key=True)
    hunger: Mapped[float] = mapped_column(default=60.0)
    cleanliness: Mapped[float] = mapped_column(default=100.0)
    growth: Mapped[float] = mapped_column(default=0.0)
    hunger_zero_since: Mapped[datetime | None] = mapped_column(UTCDateTime())
    last_computed_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)
    stage: Mapped[str] = mapped_column(String(24), default="egg")
    miss_keys: Mapped[list[list[Any]]] = mapped_column(JSON, default=list, server_default="[]")
    brain_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, server_default="{}")
    brain_params: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, server_default="{}")
    learned_weights: Mapped[bytes | None] = mapped_column(LargeBinary)
    preferences: Mapped[dict[str, float]] = mapped_column(JSON, default=dict, server_default="{}")
    skills: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, server_default="{}")


class CareEvent(Base):
    __tablename__ = "care_events"
    __table_args__ = (UniqueConstraint("user_id", "seq"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    week_id: Mapped[str] = mapped_column(ForeignKey("weeks.id"), index=True)
    seq: Mapped[int]
    kind: Mapped[str] = mapped_column(String(40))
    research_day: Mapped[int]
    slot: Mapped[str | None] = mapped_column(String(16))
    score: Mapped[float | None]
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)


class Puzzle(Base):
    __tablename__ = "puzzles"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    week_id: Mapped[str] = mapped_column(ForeignKey("weeks.id"), index=True)
    kind: Mapped[str] = mapped_column(String(40))
    params: Mapped[dict[str, Any]] = mapped_column(JSON)
    secret: Mapped[dict[str, Any]] = mapped_column(JSON)
    issued_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime())
    submitted_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    result: Mapped[dict[str, Any] | None] = mapped_column(JSON)


class Adult(Base):
    __tablename__ = "adults"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    week_id: Mapped[str] = mapped_column(ForeignKey("weeks.id"), unique=True)
    name: Mapped[str] = mapped_column(String(40))
    sex: Mapped[str] = mapped_column(String(1))
    strain: Mapped[str] = mapped_column(String(40))
    genotype: Mapped[dict[str, Any]] = mapped_column(JSON, default=default_genotype)
    mutation: Mapped[dict[str, Any] | None] = mapped_column(JSON)
    last_parent_week: Mapped[datetime | None] = mapped_column(UTCDateTime())
    stars: Mapped[int]
    traits: Mapped[list[str]] = mapped_column(JSON, default=list)
    subskills: Mapped[list[str]] = mapped_column(JSON, default=list)
    gathering: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, server_default="{}")
    level: Mapped[int] = mapped_column(default=1)
    exp: Mapped[int] = mapped_column(default=0)
    energy: Mapped[float] = mapped_column(default=100.0)
    brain_params: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    preferences: Mapped[dict[str, float]] = mapped_column(JSON, default=dict, server_default="{}")
    brain_snapshot: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, server_default="{}")
    learned_weights: Mapped[bytes | None] = mapped_column(LargeBinary)
    skills: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)


class TeamSlot(Base):
    __tablename__ = "team_slots"
    __table_args__ = (
        CheckConstraint("slot BETWEEN 0 AND 4", name="slot_range"),
        UniqueConstraint("adult_id"),
    )

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    slot: Mapped[int] = mapped_column(primary_key=True)
    adult_id: Mapped[str] = mapped_column(ForeignKey("adults.id"))
    bag: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    last_computed_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)


class SleepSession(Base):
    __tablename__ = "sleep_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True)
    started_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)
    ended_at: Mapped[datetime | None] = mapped_column(UTCDateTime())
    bonus: Mapped[int] = mapped_column(default=0)
