from __future__ import annotations

import json
from collections.abc import Awaitable, Callable
from datetime import timedelta
from hashlib import sha256
from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends, Header, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from sqlalchemy import delete
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse
from tsuyulabo_api.auth.dependencies import authenticate_user
from tsuyulabo_api.db.economy import IdempotencyKey
from tsuyulabo_api.db.operations import insert_if_absent
from tsuyulabo_api.errors import APIError, error_response
from tsuyulabo_api.services.guest_limits import check_guest
from tsuyulabo_api.services.request_body import read_body

GUEST_SCOPE = "00000000-0000-0000-0000-000000000000"
MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


def idempotency_header(key: Annotated[UUID, Header(alias="Idempotency-Key")]) -> None:
    """Expose the route-level requirement to OpenAPI and generated clients."""


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

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        if set(kwargs.get("methods") or ()) & MUTATING_METHODS:
            dependencies = list(kwargs.get("dependencies") or ())
            if not any(item.dependency is idempotency_header for item in dependencies):
                dependencies.append(Depends(idempotency_header))
            kwargs["dependencies"] = dependencies
        super().__init__(*args, **kwargs)

    def get_route_handler(self) -> Callable[[Request], Awaitable[Response]]:
        original = super().get_route_handler()

        async def handle(request: Request) -> Response:
            if request.method not in MUTATING_METHODS:
                return await original(request)
            if request.url.path == "/v1/auth/guest":
                await check_guest(request)
            key = require_key(request)
            body = await read_body(request)
            identity = (
                json.dumps(
                    [request.method, request.url.path, request.url.query], ensure_ascii=True
                ).encode()
                + b"\0"
                + body
            )
            # Use the existing path column to avoid a schema migration. Include a
            # readable prefix, but hash the complete path/query and exact body bytes.
            fingerprint = request.url.path[:420] + "#sha256=" + sha256(identity).hexdigest()
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
                        "path": fingerprint,
                        "created_at": now,
                    },
                    ["user_id", "key"],
                )
                record = await session.get(IdempotencyKey, (user_id, key))
                if not claimed and (record.method != request.method or record.path != fingerprint):
                    # Legacy records lack a fingerprint; fail closed until their TTL expires.
                    raise APIError("idempotency_key_reused", "別の操作に使用済みのキーです", 409)
                if not claimed and record.status_code != 0:
                    return JSONResponse(record.response, status_code=record.status_code)
                if claimed:
                    async with session.begin_nested() as mutation:
                        try:
                            response = await original(request)
                        except (APIError, RequestValidationError, HTTPException) as exc:
                            await mutation.rollback()
                            # Admission failures have no domain effects and must be retryable
                            # with the same key after capacity returns (rollback the claim too).
                            if isinstance(exc, APIError) and exc.code in {
                                "rate_limited",
                                "server_busy",
                            }:
                                raise
                            response = error_response(exc)
                        else:
                            if response.status_code >= 400:
                                await mutation.rollback()
                    body = json.loads(response.body) if response.body else None
                    deferred = hasattr(request.state, "after_commit") and response.status_code < 400
                    record.status_code = 0 if deferred else response.status_code
                    record.response = (
                        {"status": response.status_code, "body": body} if deferred else body
                    )
                    await session.flush()
            if not claimed:
                from tsuyulabo_api.services.deferred import wait_for_response

                return await wait_for_response(request, user_id, key)
            if deferred:
                from tsuyulabo_api.services.deferred import complete

                return await complete(request, user_id, key)
            return response

        return handle
