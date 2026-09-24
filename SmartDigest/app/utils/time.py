from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import DateTime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import TypeDecorator

from app.config import get_settings


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def digest_tz() -> ZoneInfo:
    return ZoneInfo(get_settings().digest_timezone)


def local_now() -> datetime:
    return utcnow().astimezone(digest_tz())


class UTCDateTime(TypeDecorator):
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value

    def process_result_value(self, value, dialect):
        if value is not None and value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
