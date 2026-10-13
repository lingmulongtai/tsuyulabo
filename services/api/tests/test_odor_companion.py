from __future__ import annotations

from sqlalchemy import select
from tsuyulabo_api.db.models import CareEvent
from tsuyulabo_api.routers import weeks
from tsuyulabo_api.services import behaviour_why, diary, experiments
from tsuyulabo_api.services.game import record_care

from .game_support import FakeBrain, GameClient


async def test_visible_odor_copy_is_cited_in_diary_and_contextual_why(sessions):
    class Engine:
        def run_odor_choice(self, snapshot, cue, trials, seed):
            return {"toward": trials, "away": 0}

    async with GameClient(sessions, weeks.router) as game:
        fly_id = (await game.post("/v1/weeks", {})).json()["id"]
        now = game.clock.now()
        brain = FakeBrain()
        snapshot, _ = brain.train(brain.new(), "banana", "reward", 1, 0)
        params = {
            "user_id": game.user["id"],
            "fly_id": fly_id,
            "experiment_id": "odor-1",
            "snapshot": snapshot,
            "cue": "banana",
            "trials": 1,
            "seed": 0,
            "created_at": now.isoformat(),
        }
        async with sessions() as session, session.begin():
            await record_care(
                session,
                game.user["id"],
                fly_id,
                now,
                now,
                "training",
                {"cue": "banana", "valence": "reward", "value": 0.6},
            )
            await experiments.perform(session, brain, params)
            await experiments.perform(session, brain, params)
            rows = list(
                await session.scalars(select(CareEvent).where(CareEvent.kind == "behaviour"))
            )
            assert len(rows) == 1 and rows[0].payload["cue"] == "banana"
            result = await diary.generate(session, game.user["id"], fly_id, now.date())
            assert "バナナ" in result["entry"]["text"] and "コピー" in result["entry"]["text"]
            assert "#c-1" in result["entry"]["evidence"]
            answer = await behaviour_why.explain(
                session,
                game.user["id"],
                fly_id,
                now,
                source="copy_odor_choice",
                behaviour="approach",
                brain=Engine(),
            )
            assert "コピー" in answer["text"] and "バナナ" in answer["text"]
            assert answer["text"].count("。") == 2
