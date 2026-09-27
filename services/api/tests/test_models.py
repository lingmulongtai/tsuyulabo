from __future__ import annotations

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession
from tsuyulabo_api.db.models import Base, Paper, User


async def test_all_tables_exist(engine: AsyncEngine) -> None:
    expected = {
        "users",
        "weeks",
        "larva_states",
        "care_events",
        "puzzles",
        "daily_circuit_attempts",
        "maze_races",
        "maze_entries",
        "maze_slots",
        "sumo_bouts",
        "mating_proposals",
        "pending_eggs",
        "adults",
        "team_slots",
        "inventory",
        "ledger_accounts",
        "ledger_entries",
        "idempotency_keys",
        "friendships",
        "likes",
        "gifts",
        "notifications",
        "notification_preferences",
        "push_subscriptions",
        "push_deliveries",
        "sleep_sessions",
        "shiori_messages",
        "experiments",
        "jobs",
        "papers",
    }
    async with engine.connect() as connection:
        tables = await connection.run_sync(lambda sync: inspect(sync).get_table_names())
    assert set(tables) == expected == set(Base.metadata.tables)


async def test_sqlite_json_and_utc_roundtrip(session: AsyncSession) -> None:
    user = User(display_name="test", friend_code="ABCDEFGH")
    paper = Paper(title="test", authors=["author"], year=2026, chunk="text", embedding=[0.1] * 384)
    session.add_all([user, paper])
    await session.flush()
    await session.refresh(user)
    await session.refresh(paper)
    assert user.created_at.utcoffset().total_seconds() == 0
    assert paper.embedding == [0.1] * 384
