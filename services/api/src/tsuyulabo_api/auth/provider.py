from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Protocol

import jwt
from tsuyulabo_api.errors import APIError


class AuthProvider(Protocol):
    def issue_token(self, user_id: str) -> str: ...

    def verify_token(self, token: str) -> str: ...


class GuestAuthProvider:
    def __init__(self, secret: str) -> None:
        self.secret = secret

    def issue_token(self, user_id: str) -> str:
        now = datetime.now(UTC)
        return jwt.encode(
            {"sub": user_id, "iat": now, "exp": now + timedelta(days=90)},
            self.secret,
            algorithm="HS256",
        )

    def verify_token(self, token: str) -> str:
        try:
            claims = jwt.decode(
                token, self.secret, algorithms=["HS256"], options={"require": ["sub", "iat", "exp"]}
            )
            if not isinstance(claims["sub"], str) or not claims["sub"]:
                raise jwt.InvalidTokenError("invalid subject")
            return claims["sub"]
        except jwt.InvalidTokenError as exc:
            raise APIError("unauthorized", "認証が必要です", 401) from exc
