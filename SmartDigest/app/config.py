from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_bot_token: str = ""
    telegram_mode: str = "polling"
    telegram_webhook_url: str = ""
    telegram_webhook_secret: str = "smartdigest-secret"

    database_url: str = "sqlite+aiosqlite:///./data/smartdigest.db"
    admin_telegram_ids: str = ""

    free_max_sources: int = 5
    vip_max_sources: int = 40
    free_interval_seconds: int = 3600
    vip_interval_seconds: int = 900
    collect_tick_seconds: int = 60
    digest_window_hours: int = 24
    digest_timezone: str = "Europe/Moscow"
    default_digest_hour: int = 9
    free_digest_items: int = 12
    vip_digest_items: int = 30
    http_timeout: float = 25.0
    http_proxy: str = ""
    user_agent: str = (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )

    @property
    def admin_ids(self) -> set[int]:
        ids: set[int] = set()
        for chunk in self.admin_telegram_ids.split(","):
            chunk = chunk.strip()
            if chunk.isdigit():
                ids.add(int(chunk))
        return ids


@lru_cache
def get_settings() -> Settings:
    return Settings()
