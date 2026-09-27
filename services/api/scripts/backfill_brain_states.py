"""Run after Alembic upgrades, before serving legacy replay-based databases."""

from __future__ import annotations

import asyncio

from sqlalchemy import select
from tsuyulabo_api.brain_adapter import BrainAdapter
from tsuyulabo_api.db.models import Adult, LarvaState
from tsuyulabo_api.db.session import create_engine, session_factory
from tsuyulabo_api.services.brain_state import snapshot, store
from tsuyulabo_api.settings import Settings


async def main() -> None:
    engine = create_engine(Settings().database_url)
    brain = BrainAdapter()
    try:
        async with session_factory(engine)() as session, session.begin():
            for model in (LarvaState, Adult):
                for row in await session.scalars(select(model).with_for_update()):
                    if row.learned_weights is not None and row.preferences:
                        continue
                    state = snapshot(row)
                    store(row, brain.encode(brain.restore(state), state.get("training", [])), brain)
    finally:
        await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
