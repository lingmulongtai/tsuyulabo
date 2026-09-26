from __future__ import annotations

from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    database_url: str = "sqlite+aiosqlite:///./tsuyulabo.db"
    redis_url: str | None = None
    jwt_secret: SecretStr = SecretStr("local-development-only-change-before-deploying")
    dev_tools: bool = Field(default=False, validation_alias="TSUYU_DEV_TOOLS")
    brain_mode: Literal["inline", "queue"] = "inline"
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
