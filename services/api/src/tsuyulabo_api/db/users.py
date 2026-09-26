from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from tsuyulabo_api.db.base import Base, UTCDateTime, new_id, utc_now


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    display_name: Mapped[str] = mapped_column(String(40))
    friend_code: Mapped[str] = mapped_column(String(8), unique=True)
    title: Mapped[str | None] = mapped_column(String(100))
    favorite_adult_id: Mapped[str | None] = mapped_column(
        ForeignKey("adults.id", use_alter=True, name="fk_users_favorite_adult_id_adults")
    )
    dev_time_offset_s: Mapped[int] = mapped_column(BigInteger, default=0)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime(), default=utc_now)
