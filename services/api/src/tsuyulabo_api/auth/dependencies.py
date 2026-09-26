from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession
from tsuyulabo_api.db.session import get_session
from tsuyulabo_api.db.users import User
from tsuyulabo_api.errors import APIError


async def authenticate_user(request: Request, session: AsyncSession) -> User:
    authorization = request.headers.get("authorization", "")
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise APIError("unauthorized", "認証が必要です", 401)
    user_id = request.app.state.auth_provider.verify_token(token)
    user = await session.get(User, user_id)
    if user is None:
        raise APIError("unauthorized", "認証が必要です", 401)
    return user


async def get_current_user(
    request: Request, session: Annotated[AsyncSession, Depends(get_session)]
) -> User:
    return await authenticate_user(request, session)
