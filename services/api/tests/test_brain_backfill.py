from __future__ import annotations

import runpy
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from tsuyulabo_api.db.models import Adult, LarvaState, User, Week
from tsuyulabo_api.services.brain_state import snapshot

from .game_support import FakeBrain


async def test_backfill_converts_legacy_rows_once(sessions: Any) -> None:
    legacy = {
        "default": True,
        "individual": {},
        "training": [{"cue": "banana", "valence": "reward", "strength": 0.36, "seed": 7}],
    }
    async with sessions() as session, session.begin():
        session.add(User(id="legacy-user", display_name="test", friend_code="ABCDEFGH"))
        await session.flush()
        session.add(Week(id="legacy-week", user_id="legacy-user"))
        await session.flush()
        session.add(LarvaState(week_id="legacy-week", brain_snapshot=legacy))
        session.add(
            Adult(
                id="legacy-adult",
                user_id="legacy-user",
                week_id="legacy-week",
                name="test",
                sex="f",
                strain="wild",
                stars=1,
                brain_snapshot=legacy,
            )
        )
    script = Path(__file__).parents[1] / "scripts/backfill_brain_states.py"
    main = runpy.run_path(str(script))["main"]
    main.__globals__["Settings"] = lambda: SimpleNamespace(
        database_url=str(sessions.kw["bind"].url)
    )
    main.__globals__["BrainAdapter"] = FakeBrain
    await main()
    async with sessions() as session:
        for model, key in [(LarvaState, "legacy-week"), (Adult, "legacy-adult")]:
            row = await session.get(model, key)
            assert row.learned_weights and row.preferences["banana"] == 0.36
            assert row.brain_snapshot == {"training": legacy["training"]}
            assert FakeBrain().restore(snapshot(row)).values["banana"] == 0.36
        before = row.learned_weights
    await main()
    async with sessions() as session:
        assert (await session.get(Adult, "legacy-adult")).learned_weights == before
