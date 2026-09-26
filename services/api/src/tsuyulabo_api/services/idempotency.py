from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from datetime import timedelta
from uuid import UUID

from fastapi import Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from sqlalchemy import delete
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from tsuyulabo_api.auth.dependencies import authenticate_user
from tsuyulabo_api.db.economy import IdempotencyKey
from tsuyulabo_api.db.operations import insert_if_absent
from tsuyulabo_api.errors import APIError, error_response

GUEST_SCOPE = "00000000-0000-0000-0000-000000000000"
MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def require_key(request: Request) -> str:
    value = request.headers.get("idempotency-key")
    if not value:
        raise APIError("idempotency_key_required", "Idempotency-Key が必要です", 400)
    try:
        return str(UUID(value))
    except ValueError as exc:
        raise APIError(
            "validation_error", "Idempotency-Key は UUID で指定してください", 422
        ) from exc


class IdempotentRoute(APIRoute):
    """Commit a mutation and its replay record together, before sending the response.

    Handlers must use get_session and must not commit themselves. External effects
    require an outbox/worker transaction; a SQL transaction cannot roll Redis back.
    """

    def get_route_handler(self) -> Callable[[Request], Awaitable[Response]]:
        original = super().get_route_handler()

        async def handle(request: Request) -> Response:
            if request.method not in MUTATING_METHODS:
                return await original(request)
            key = require_key(request)
            async with request.app.state.session_factory() as session, session.begin():
                request.state.session = session
                if request.url.path == "/v1/auth/guest":
                    user_id = GUEST_SCOPE
                else:
                    user_id = (await authenticate_user(request, session)).id
                now = request.app.state.clock.now()
                await session.execute(
                    delete(IdempotencyKey).where(
                        IdempotencyKey.created_at <= now - timedelta(hours=24)
                    )
                )
                claimed = await insert_if_absent(
                    session,
                    IdempotencyKey,
                    {
                        "user_id": user_id,
                        "key": key,
                        "method": request.method,
                        "path": request.url.path,
                        "created_at": now,
                    },
                    ["user_id", "key"],
                )
                record = await session.get(IdempotencyKey, (user_id, key))
                if not claimed:
                    return JSONResponse(record.response, status_code=record.status_code)
                async with session.begin_nested() as mutation:
                    try:
                        response = await original(request)
                    except (APIError, RequestValidationError, HTTPException) as exc:
                        await mutation.rollback()
                        response = error_response(exc)
                    else:
                        if response.status_code >= 400:
                            await mutation.rollback()
                # Foundation mutation endpoints return JSON (or an empty 204 response).
                body = json.loads(response.body) if response.body else None
                record.status_code = response.status_code
                record.response = body
                await session.flush()
            return response

        return handle
