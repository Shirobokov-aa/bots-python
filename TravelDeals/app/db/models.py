from datetime import datetime

from sqlalchemy import BigInteger, Boolean, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.utils.time import TimestampMixin, UTCDateTime


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)

    alerts: Mapped[list["PriceAlert"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class PriceAlert(Base, TimestampMixin):
    __tablename__ = "price_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    origin: Mapped[str] = mapped_column(String(8))
    destination: Mapped[str] = mapped_column(String(8))
    max_price: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_notified_price: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_notified_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    user: Mapped[User] = relationship(back_populates="alerts")


class PostedDeal(Base, TimestampMixin):
    __tablename__ = "posted_deals"
    __table_args__ = (UniqueConstraint("dedupe_key", name="uq_posted_dedupe"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    dedupe_key: Mapped[str] = mapped_column(String(128), index=True)
    deal_type: Mapped[str] = mapped_column(String(16))
    title: Mapped[str] = mapped_column(String(512))
    price: Mapped[int] = mapped_column(Integer)
    link: Mapped[str] = mapped_column(Text)
    posted_to_channel: Mapped[bool] = mapped_column(Boolean, default=False)
