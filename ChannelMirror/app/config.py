from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

_WEAK_WEBHOOK_SECRETS = frozenset({"", "change-me", "channelmirror-secret"})


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    telegram_bot_token: str = ""
    telegram_mode: str = "polling"
    telegram_webhook_url: str = ""
    # Empty by default — set a strong value when TELEGRAM_MODE=webhook
    telegram_webhook_secret: str = ""

    # Telethon user-client (read public sources)
    telegram_api_id: int = 0
    telegram_api_hash: str = ""
    telegram_session: str = ""  # StringSession; empty = listener off

    database_url: str = "sqlite+aiosqlite:///./data/channelmirror.db"
    # Required in prod: comma-separated Telegram user ids. Empty = deny all.
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

    def validate_runtime(self) -> None:
        """Raise if misconfigured for a safe start."""
        if not self.admin_ids:
            raise RuntimeError(
                "ADMIN_TELEGRAM_IDS пустой — откажемся стартовать (иначе бот открыт всем)"
            )
        if self.telegram_mode == "webhook":
            if not self.telegram_webhook_url:
                raise RuntimeError("TELEGRAM_WEBHOOK_URL нужен для webhook")
            secret = (self.telegram_webhook_secret or "").strip()
            if secret in _WEAK_WEBHOOK_SECRETS or len(secret) < 16:
                raise RuntimeError(
                    "TELEGRAM_WEBHOOK_SECRET слишком слабый — задай случайную строку ≥16"
                )


@lru_cache
def get_settings() -> Settings:
    return Settings()
