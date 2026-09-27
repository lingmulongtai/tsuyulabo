"""Shiori answer handler shared by inline API execution and the queue worker."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from tsuyu_shiori.features import answer_question
from tsuyu_shiori.gateway import Provider
from tsuyulabo_api.db.models import ShioriMessage
from tsuyulabo_api.services.jobs import JobFunction
from tsuyulabo_api.services.shiori_brain import BrainEngine
from tsuyulabo_api.services.shiori_store import SQLLab, SQLRecordStore, conversation_scope


async def perform(
    session: AsyncSession,
    user_id: str,
    params: dict[str, Any],
    provider: Provider | None = None,
    brain: BrainEngine | None = None,
) -> dict[str, Any]:
    store = SQLRecordStore(session, user_id)
    week_id, fly_id = await conversation_scope(store, params)
    question = params.get("question")
    if not isinstance(question, str):
        raise ValueError("question is required")
    answer = await answer_question(
        question,
        store=store,
        lab=SQLLab(session, user_id, brain),
        week_id=week_id,
        fly_id=fly_id,
        provider=provider,
    )
    timestamps = (
        {"created_at": datetime.fromisoformat(params["game_now"])} if params.get("game_now") else {}
    )
    session.add_all(
        [
            ShioriMessage(
                user_id=user_id, role="user", text=question, evidence=[], cost={}, **timestamps
            ),
            ShioriMessage(
                user_id=user_id,
                role="assistant",
                text=answer.text,
                evidence=answer.evidence_ids,
                cost=answer.cost,
                **timestamps,
            ),
        ]
    )
    await session.flush()
    return answer.to_dict()


def handler(
    sessions: async_sessionmaker[AsyncSession], provider: Provider | None = None
) -> JobFunction:
    async def run(params: dict[str, Any]) -> dict[str, Any]:
        async with sessions() as session, session.begin():
            # user_id is inserted by the authenticated route, never supplied by the model.
            return await perform(session, params["user_id"], params, provider)

    return run
