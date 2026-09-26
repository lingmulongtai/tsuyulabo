from __future__ import annotations

import secrets
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from tsuyulabo_api.auth.dependencies import get_current_user
from tsuyulabo_api.db.models import Adult, User
from tsuyulabo_api.db.session import get_session
from tsuyulabo_api.errors import APIError
from tsuyulabo_api.services.idempotency import IdempotentRoute
from tsuyulabo_api.services.ledger import balances, get_account, transfer

router = APIRouter(prefix="/v1", route_class=IdempotentRoute)
Session = Annotated[AsyncSession, Depends(get_session)]
CurrentUser = Annotated[User, Depends(get_current_user)]
FRIEND_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


class GuestRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    display_name: str = Field(min_length=1, max_length=40)


class ProfilePatch(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    display_name: str | None = Field(default=None, min_length=1, max_length=40)
    title: str | None = Field(default=None, max_length=100)
    favorite_adult_id: UUID | None = None

    @field_validator("display_name")
    @classmethod
    def name_cannot_be_null(cls, value: str | None) -> str:
        if value is None:
            raise ValueError("display_name cannot be null")
        return value


async def profile(session: AsyncSession, user: User) -> dict[str, Any]:
    return {
        "id": user.id,
        "display_name": user.display_name,
        "friend_code": user.friend_code,
        "title": user.title,
        "favorite_adult_id": user.favorite_adult_id,
        "balances": await balances(session, user.id),
        "research_rank": None,
    }


@router.post("/auth/guest", status_code=201)
async def create_guest(body: GuestRequest, request: Request, session: Session) -> dict[str, Any]:
    for _ in range(10):
        user = User(
            display_name=body.display_name,
            friend_code="".join(secrets.choice(FRIEND_CODE_ALPHABET) for _ in range(8)),
        )
        try:
            async with session.begin_nested():
                session.add(user)
                await session.flush()
            break
        except IntegrityError:
            # A generated friend code may collide; uniqueness is decided by the DB.
            continue
    else:
        raise APIError("internal_error", "ユーザーを作成できませんでした", 500)
    source = await get_account(session, "system:rewards", "shizuku")
    wallet = await get_account(session, f"user:{user.id}", "shizuku")
    await transfer(session, source, wallet, 300, "initial_grant", user.id)
    return {
        "user": await profile(session, user),
        "token": request.app.state.auth_provider.issue_token(user.id),
    }


@router.get("/me")
async def get_me(user: CurrentUser, session: Session) -> dict[str, Any]:
    return await profile(session, user)


@router.patch("/me")
async def patch_me(body: ProfilePatch, user: CurrentUser, session: Session) -> dict[str, Any]:
    fields = body.model_fields_set
    if "favorite_adult_id" in fields and body.favorite_adult_id is not None:
        adult = await session.get(Adult, str(body.favorite_adult_id))
        if adult is None or adult.user_id != user.id:
            raise APIError("not_found", "成虫が見つかりません", 404)
    for name, value in body.model_dump(exclude_unset=True, mode="json").items():
        setattr(user, name, value)
    await session.flush()
    return await profile(session, user)
