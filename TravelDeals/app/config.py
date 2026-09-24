from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_bot_token: str = ""
    telegram_mode: str = "polling"
    telegram_webhook_url: str = ""
    telegram_webhook_secret: str = "traveldeals-secret"
    telegram_channel_id: str = ""

    database_url: str = "sqlite+aiosqlite:///./data/traveldeals.db"
    admin_telegram_ids: str = ""

    travelpayouts_token: str = ""
    travelpayouts_marker: str = ""

    deal_tick_seconds: int = 3600
    http_timeout: float = 25.0
    channel_link: str = ""
    routes_file: str = "routes.yaml"

    @property
    def admin_ids(self) -> set[int]:
        ids: set[int] = set()
        for chunk in self.admin_telegram_ids.split(","):
            chunk = chunk.strip()
            if chunk.isdigit():
                ids.add(int(chunk))
        return ids

    @property
    def channel_chat_id(self) -> int | None:
        raw = self.telegram_channel_id.strip()
        if not raw:
            return None
        try:
            return int(raw)
        except ValueError:
            return None


@lru_cache
def get_settings() -> Settings:
    return Settings()
