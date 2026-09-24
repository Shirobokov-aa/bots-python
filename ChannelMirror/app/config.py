from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_bot_token: str = ""
    telegram_mode: str = "polling"
    telegram_webhook_url: str = ""
    telegram_webhook_secret: str = "channelmirror-secret"

    # Telethon user-client (read public sources)
    telegram_api_id: int = 0
    telegram_api_hash: str = ""
    telegram_session: str = ""  # StringSession; empty = listener off

    database_url: str = "sqlite+aiosqlite:///./data/channelmirror.db"
    admin_telegram_ids: str = ""

    # Publish spacing per destination (1–2h default)
    post_interval_seconds: int = 5400
    publish_tick_seconds: int = 30
    album_wait_seconds: float = 1.2
    media_dir: str = "data/media"

    @property
    def admin_ids(self) -> set[int]:
        ids: set[int] = set()
        for chunk in self.admin_telegram_ids.split(","):
            chunk = chunk.strip()
            if chunk.isdigit():
                ids.add(int(chunk))
        return ids

    @property
    def telethon_ready(self) -> bool:
        return bool(self.telegram_api_id and self.telegram_api_hash and self.telegram_session)


@lru_cache
def get_settings() -> Settings:
    return Settings()
