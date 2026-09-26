from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
import pytest
from tsuyulabo_api.auth.provider import GuestAuthProvider
from tsuyulabo_api.errors import APIError

SECRET = "a-test-secret-with-at-least-48-bytes-for-hs384-rejection"


def test_token_lifetime_and_rejection() -> None:
    provider = GuestAuthProvider(SECRET)
    token = provider.issue_token("user-id")
    assert provider.verify_token(token) == "user-id"
    claims = jwt.decode(token, SECRET, algorithms=["HS256"])
    assert claims["exp"] - claims["iat"] == 90 * 86400
    expired = jwt.encode(
        {
            "sub": "user-id",
            "iat": datetime.now(UTC) - timedelta(days=91),
            "exp": datetime.now(UTC) - timedelta(days=1),
        },
        SECRET,
        algorithm="HS256",
    )
    wrong_algorithm = jwt.encode(claims, SECRET, algorithm="HS384")
    missing_expiry = jwt.encode({"sub": "user-id"}, SECRET, algorithm="HS256")
    for invalid in [
        "bad-token",
        expired,
        wrong_algorithm,
        missing_expiry,
        GuestAuthProvider("another-secret-with-at-least-32-bytes").issue_token("user-id"),
    ]:
        with pytest.raises(APIError) as error:
            provider.verify_token(invalid)
        assert error.value.code == "unauthorized"
