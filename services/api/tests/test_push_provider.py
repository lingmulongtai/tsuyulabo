from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import pytest
import requests
from cryptography.hazmat.primitives import serialization
from py_vapid import Vapid02
from pywebpush import WebPushException
from tsuyulabo_api.db.push import PushSubscription
from tsuyulabo_api.services.push import (
    NoRedirectSession,
    WebPushSender,
    decode_key,
    validate_endpoint,
)
from tsuyulabo_api.settings import Settings


@pytest.mark.parametrize(
    "endpoint",
    [
        "http://fcm.googleapis.com/x",
        "https://127.0.0.1/x",
        "https://localhost/x",
        "https://fcm.googleapis.com.evil.test/x",
        "https://evil.test/push.apple.com/x",
        "https://user:pass@fcm.googleapis.com/x",
        "https://fcm.googleapis.com:8443/x",
        "https://fcm.googleapis.com/x#fragment",
    ],
)
def test_reject_non_push_endpoints(endpoint: str) -> None:
    with pytest.raises(ValueError):
        validate_endpoint(endpoint)


async def test_provider_encrypts_with_bounded_delivery_and_maps_dead_status() -> None:
    settings = Settings(vapid_public_key="public", vapid_private_key="private", _env_file=None)
    sender = WebPushSender(settings)
    subscription = PushSubscription(
        endpoint="https://fcm.googleapis.com/push/test", p256dh="key", auth="auth"
    )
    response = requests.Response()
    response.status_code = 410
    with patch(
        "tsuyulabo_api.services.push.webpush",
        side_effect=WebPushException("gone", response=response),
    ) as send:
        assert await sender.send(subscription, {"title": "ごはんの時間です"}) == 410
        kwargs = send.call_args.kwargs
        assert kwargs["content_encoding"] == "aes128gcm"
        assert kwargs["ttl"] == 300 and kwargs["timeout"] == 10
        assert json.loads(kwargs["data"])["title"] == "ごはんの時間です"
        assert kwargs["vapid_claims"] == {"sub": settings.vapid_subject}
    with patch.object(requests.Session, "request", return_value=response) as request:
        NoRedirectSession().post(subscription.endpoint)
        assert request.call_args.kwargs["allow_redirects"] is False


def test_key_helper_writes_matching_keys_and_refuses_rotation(tmp_path: Path) -> None:
    spec = importlib.util.spec_from_file_location(
        "generate_vapid", Path(__file__).parents[1] / "scripts/generate_vapid.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    path = tmp_path / ".env"
    path.write_text("EXISTING=value\n", encoding="utf-8")
    module.generate(path, "mailto:local@example.com")
    settings = Settings(_env_file=path)
    key = Vapid02.from_string(settings.vapid_private_key.get_secret_value())
    assert key.public_key.public_bytes(
        serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint
    ) == decode_key(settings.vapid_public_key)
    original = path.read_bytes()
    with pytest.raises(ValueError):
        module.generate(path, "mailto:local@example.com")
    assert path.read_bytes() == original
    assert "EXISTING=value" in path.read_text()
