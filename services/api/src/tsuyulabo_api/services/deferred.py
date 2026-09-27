"""Finalize a post-commit calculation without changing an already replayable response."""

from __future__ import annotations

import asyncio
from contextlib import suppress
from time import monotonic
from typing import Any

from fastapi import Request
from sqlalchemy import select
from starlette.responses import JSONResponse
from tsuyulabo_api.db.models import IdempotencyKey

LEARNING_WAIT_SECONDS = 3


async def finalize(request: Request, user_id: str, key: str, body: Any = None) -> JSONResponse:
    async with request.app.state.session_factory() as session, session.begin():
        record = await session.scalar(
            select(IdempotencyKey)
            .where(IdempotencyKey.user_id == user_id, IdempotencyKey.key == key)
            .with_for_update()
        )
        if record.status_code == 0:
            provisional = record.response
            record.status_code = provisional["status"]
            record.response = provisional["body"] if body is None else body
        return JSONResponse(record.response, status_code=record.status_code)


async def wait_for_response(request: Request, user_id: str, key: str) -> JSONResponse:
    # A crashed originator still has an accepted, persisted provisional response.
    # Replays can safely expose it after the computation's three-second deadline.
    deadline = monotonic() + LEARNING_WAIT_SECONDS + 0.5
    while monotonic() < deadline:
        async with request.app.state.session_factory() as session:
            record = await session.get(IdempotencyKey, (user_id, key))
            if record.status_code != 0:
                return JSONResponse(record.response, status_code=record.status_code)
        await asyncio.sleep(0.05)
    return await finalize(request, user_id, key)


async def complete(request: Request, user_id: str, key: str) -> JSONResponse:
    task = asyncio.create_task(request.state.after_commit())
    pending = getattr(request.app.state, "pending_calculations", None)
    if pending is None:
        pending = request.app.state.pending_calculations = set()
    pending.add(task)

    def finished(task: asyncio.Task) -> None:
        pending.discard(task)
        if not task.cancelled():
            task.exception()  # Retrieve exceptions after a response timeout too.

    task.add_done_callback(finished)
    body = None
    # A timeout never cancels the accepted job; later reads expose its learning.
    with suppress(Exception):
        body = await asyncio.wait_for(asyncio.shield(task), timeout=LEARNING_WAIT_SECONDS)
    return await finalize(request, user_id, key, body)
