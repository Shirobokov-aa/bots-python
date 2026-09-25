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

    destinations: Mapped[list["Destination"]] = relationship(back_populates="user")
    sources: Mapped[list["Source"]] = relationship(back_populates="user")
    routes: Mapped[list["Route"]] = relationship(back_populates="user")


class Destination(Base, TimestampMixin):
    """Own channel where the bot posts (silent copy)."""

    __tablename__ = "destinations"
    __table_args__ = (UniqueConstraint("user_id", "chat_id", name="uq_user_dest_chat"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_posted_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    user: Mapped[User] = relationship(back_populates="destinations")
    routes: Mapped[list["Route"]] = relationship(back_populates="destination")


class Source(Base, TimestampMixin):
    """TG channel to mirror (public @username and/or chat_id)."""

    __tablename__ = "sources"
    __table_args__ = (UniqueConstraint("user_id", "username", name="uq_user_source_username"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    username: Mapped[str] = mapped_column(String(64), index=True)
    # Telegram peer id (-100…); set after Telethon resolve — needed when channel has no @
    chat_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True, index=True)
    title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    user: Mapped[User] = relationship(back_populates="sources")
    routes: Mapped[list["Route"]] = relationship(back_populates="source")


class Route(Base, TimestampMixin):
    """source → destination mapping."""

    __tablename__ = "routes"
    __table_args__ = (UniqueConstraint("source_id", "destination_id", name="uq_source_dest"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True)
    destination_id: Mapped[int] = mapped_column(ForeignKey("destinations.id", ondelete="CASCADE"), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    interval_seconds: Mapped[int] = mapped_column(Integer, default=5400)
    # If True — append plain-text footer: Источник: "Channel Title" (no link).
    show_source_label: Mapped[bool] = mapped_column(Boolean, default=False)

    user: Mapped[User] = relationship(back_populates="routes")
    source: Mapped[Source] = relationship(back_populates="routes")
    destination: Mapped[Destination] = relationship(back_populates="routes")
    queue_items: Mapped[list["QueueItem"]] = relationship(back_populates="route", cascade="all, delete-orphan")


class SeenPost(Base):
    __tablename__ = "seen_posts"
    __table_args__ = (UniqueConstraint("source_id", "message_id", name="uq_source_msg"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id", ondelete="CASCADE"), index=True)
    message_id: Mapped[int] = mapped_column(Integer)
    grouped_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    seen_at: Mapped[datetime] = mapped_column(UTCDateTime)


class QueueItem(Base, TimestampMixin):
    __tablename__ = "queue_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    route_id: Mapped[int] = mapped_column(ForeignKey("routes.id", ondelete="CASCADE"), index=True)
    source_message_id: Mapped[int] = mapped_column(Integer)
    # pending | posted | failed | skipped
    status: Mapped[str] = mapped_column(String(16), default="pending", index=True)
    # JSON payload: type, text, media paths, etc. Silent copy — no source attribution.
    payload_json: Mapped[str] = mapped_column(Text)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    posted_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)

    route: Mapped[Route] = relationship(back_populates="queue_items")
