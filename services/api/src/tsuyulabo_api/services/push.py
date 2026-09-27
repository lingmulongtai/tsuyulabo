"""Provider boundary: a future FCM sender can implement PushSender."""

from __future__ import annotations

import asyncio
import base64
import json
import re
from typing import Protocol
from urllib.parse import urlsplit

import requests
from pywebpush import WebPushException, webpush
from tsuyulabo_api.db.push import PushSubscription
from tsuyulabo_api.settings import Settings


def validate_endpoint(endpoint: str) -> str:
    url = urlsplit(endpoint)
    host = url.hostname or ""
    allowed = host in {"fcm.googleapis.com", "updates.push.services.mozilla.com"} or any(
        host.endswith(suffix)
        for suffix in (".push.services.mozilla.com", ".push.apple.com", ".notify.windows.com")
    )
    if (
        not allowed
        or url.scheme != "https"
        or url.port not in (None, 443)
        or url.username
        or url.password
        or url.fragment
        or not url.path
    ):
        raise ValueError("endpoint must be an HTTPS browser push service URL")
    return endpoint


def decode_key(value: str) -> bytes:
    if not re.fullmatch(r"[A-Za-z0-9_-]+", value):
        raise ValueError("invalid base64url key")
    return base64.urlsafe_b64decode(value + "=" * (-len(value) % 4))


class PushSender(Protocol):
    async def send(self, subscription: PushSubscription, payload: dict[str, str]) -> int:
        """Return the provider HTTP status; 404/410 mean an expired subscription."""
        ...


class NoRedirectSession(requests.Session):
    def request(self, method: str, url: str, **kwargs: object) -> requests.Response:
        kwargs["allow_redirects"] = False
        return super().request(method, url, **kwargs)


class WebPushSender:
    def __init__(self, settings: Settings) -> None:
        if not settings.vapid_public_key or not settings.vapid_private_key:
            raise ValueError("VAPID keys are not configured")
        self.settings = settings

    async def send(self, subscription: PushSubscription, payload: dict[str, str]) -> int:
        return await asyncio.to_thread(self._send, subscription, payload)

    def _send(self, subscription: PushSubscription, payload: dict[str, str]) -> int:
        validate_endpoint(subscription.endpoint)
        with NoRedirectSession() as session:
            try:
                response = webpush(
                    subscription_info={
                        "endpoint": subscription.endpoint,
                        "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
                    },
                    data=json.dumps(payload, ensure_ascii=False),
                    vapid_private_key=self.settings.vapid_private_key.get_secret_value(),
                    vapid_claims={"sub": self.settings.vapid_subject},
                    content_encoding="aes128gcm",
                    ttl=300,
                    timeout=10,
                    requests_session=session,
                )
                return response.status_code
            except WebPushException as error:
                if error.response is not None:
                    return error.response.status_code
                raise RuntimeError("push transport failed") from None
