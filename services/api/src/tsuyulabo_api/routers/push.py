from __future__ import annotations

from cryptography.hazmat.primitives.asymmetric import ec
from fastapi import APIRouter, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import delete, func, select
from tsuyulabo_api.db.push import NotificationPreference, PushSubscription
from tsuyulabo_api.errors import APIError
from tsuyulabo_api.services.game import CurrentUser, Session
from tsuyulabo_api.services.idempotency import IdempotentRoute
from tsuyulabo_api.services.push import decode_key, validate_endpoint
from tsuyulabo_api.services.push_preferences import PushPreferences

router = APIRouter(prefix="/v1/push", route_class=IdempotentRoute)


class EndpointRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    endpoint: str = Field(max_length=2048)

    @field_validator("endpoint")
    @classmethod
    def endpoint_url(cls, value: str) -> str:
        return validate_endpoint(value)


class SubscriptionKeys(BaseModel):
    model_config = ConfigDict(extra="forbid")
    p256dh: str = Field(max_length=100)
    auth: str = Field(max_length=32)

    @field_validator("p256dh")
    @classmethod
    def public_key(cls, value: str) -> str:
        key = decode_key(value)
        if len(key) != 65 or key[0] != 4:
            raise ValueError("expected uncompressed P-256 public key")
        ec.EllipticCurvePublicKey.from_encoded_point(ec.SECP256R1(), key)
        return value

    @field_validator("auth")
    @classmethod
    def auth_secret(cls, value: str) -> str:
        if len(decode_key(value)) != 16:
            raise ValueError("expected 16-byte authentication secret")
        return value


class SubscribeRequest(EndpointRequest):
    keys: SubscriptionKeys
    expirationTime: float | None = None


class PublicKeyResponse(BaseModel):
    public_key: str | None


class SubscriptionResponse(BaseModel):
    subscribed: bool


@router.get("/public-key")
async def public_key(request: Request) -> PublicKeyResponse:
    settings = request.app.state.settings
    return PublicKeyResponse(
        public_key=settings.vapid_public_key if settings.vapid_private_key else None
    )


@router.get("/preferences")
async def preferences(user: CurrentUser, session: Session) -> PushPreferences:
    row = await session.get(NotificationPreference, user.id)
    return PushPreferences.model_validate(row.preferences if row else {})


@router.put("/preferences")
async def update_preferences(
    body: PushPreferences, user: CurrentUser, session: Session
) -> PushPreferences:
    row = await session.get(NotificationPreference, user.id)
    if row is None:
        session.add(NotificationPreference(user_id=user.id, preferences=body.model_dump()))
    else:
        row.preferences = body.model_dump()
    return body


@router.post("/subscribe")
async def subscribe(
    body: SubscribeRequest, user: CurrentUser, session: Session, request: Request
) -> SubscriptionResponse:
    settings = request.app.state.settings
    if not settings.vapid_public_key or not settings.vapid_private_key:
        raise APIError("push_unavailable", "通知の準備中です", 503)
    row = await session.scalar(
        select(PushSubscription).where(PushSubscription.endpoint == body.endpoint)
    )
    if row is not None and row.user_id != user.id:
        raise APIError("subscription_conflict", "このブラウザーは別の研究員に登録されています", 409)
    if row is None:
        count = await session.scalar(
            select(func.count())
            .select_from(PushSubscription)
            .where(PushSubscription.user_id == user.id)
        )
        if count >= 10:
            raise APIError("subscription_limit", "通知を登録できる端末は10台までです", 409)
        row = PushSubscription(user_id=user.id, endpoint=body.endpoint)
        session.add(row)
    row.p256dh, row.auth = body.keys.p256dh, body.keys.auth
    await session.flush()
    return SubscriptionResponse(subscribed=True)


@router.delete("/subscribe")
async def unsubscribe(
    body: EndpointRequest, user: CurrentUser, session: Session
) -> SubscriptionResponse:
    await session.execute(
        delete(PushSubscription).where(
            PushSubscription.user_id == user.id, PushSubscription.endpoint == body.endpoint
        )
    )
    return SubscriptionResponse(subscribed=False)
