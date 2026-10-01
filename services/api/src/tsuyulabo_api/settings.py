from __future__ import annotations

from typing import Literal, Self

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    database_url: str = "sqlite+aiosqlite:///./tsuyulabo.db"
    environment: Literal["development", "test", "production"] = Field(
        default="development", validation_alias="TSUYU_ENV"
    )
    redis_url: str | None = None
    rate_limits_enabled: bool = True
    trusted_proxy_hops: int = Field(default=1, ge=0, le=16)
    rate_guest_hour: int = Field(default=5, ge=1)
    rate_guest_day_global: int = Field(default=200, ge=1)
    rate_guest_fallback_hour_global: int = Field(default=10, ge=1)
    rate_shiori_minute: int = Field(default=10, ge=1)
    rate_shiori_day: int = Field(default=100, ge=1)
    rate_brain_minute: int = Field(default=20, ge=1)
    rate_puzzle_minute: int = Field(default=60, ge=1)
    rate_friends_minute: int = Field(default=30, ge=1)
    rate_authenticated_minute: int = Field(default=300, ge=1)
    job_max_per_user: int = Field(default=2, ge=1)
    job_max_total: int = Field(default=20, ge=1)
    job_busy_retry_after: int = Field(default=10, ge=1)
    jwt_secret: SecretStr = SecretStr("local-development-only-change-before-deploying")
    dev_tools: bool = Field(default=False, validation_alias="TSUYU_DEV_TOOLS")
    brain_mode: Literal["inline", "queue"] = "inline"
    vapid_public_key: str | None = None
    vapid_private_key: SecretStr | None = None
    vapid_subject: str = "mailto:admin@example.com"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    @model_validator(mode="after")
    def production_secret(self) -> Self:
        secret = self.jwt_secret.get_secret_value()
        if self.environment == "production" and (
            len(secret.encode("utf-8")) < 32
            or secret == "local-development-only-change-before-deploying"
        ):
            raise ValueError("JWT_SECRET must be explicitly set to at least 32 bytes in production")
        return self
