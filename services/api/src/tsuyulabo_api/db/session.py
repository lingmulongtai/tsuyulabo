from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from fastapi import Request
from sqlalchemy import Connection, event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_engine(database_url: str) -> AsyncEngine:
    engine = create_async_engine(database_url)
    if engine.dialect.name == "sqlite":

        @event.listens_for(engine.sync_engine, "connect")
        def configure_sqlite(connection: Any, _: object) -> None:
            connection.isolation_level = None
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.execute("PRAGMA busy_timeout=30000")
            cursor.close()

        @event.listens_for(engine.sync_engine, "begin")
        def begin_sqlite(connection: Connection) -> None:
            # Explicit transactions also make SAVEPOINT rollback reliable. SQLite has
            # one writer; claim it before reading to avoid read-to-write upgrade races.
            connection.exec_driver_sql("BEGIN IMMEDIATE")

    return engine


def session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, expire_on_commit=False)


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    # Mutations reuse the transaction owned by the idempotent route handler.
    if hasattr(request.state, "session"):
        yield request.state.session
    else:
        async with request.app.state.session_factory() as session, session.begin():
            yield session
