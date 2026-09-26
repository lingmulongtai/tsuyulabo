from __future__ import annotations

from typing import Any

from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession
from tsuyulabo_api.db.base import Base


async def insert_if_absent(
    session: AsyncSession, model: type[Base], values: dict[str, Any], keys: list[str]
) -> bool:
    """Use a database uniqueness check, including across API processes."""
    insert = sqlite_insert if session.get_bind().dialect.name == "sqlite" else postgres_insert
    statement = insert(model).values(**values).on_conflict_do_nothing(index_elements=keys)
    result = await session.execute(statement.returning(*model.__table__.primary_key.columns))
    return result.first() is not None
