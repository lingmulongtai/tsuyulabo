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
    jwt_secret: SecretStr = SecretStr("local-development-only-change-before-deploying")
    dev_tools: bool = Field(default=False, validation_alias="TSUYU_DEV_TOOLS")
    brain_mode: Literal["inline", "queue"] = "inline"
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
