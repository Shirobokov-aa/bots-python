from __future__ import annotations

import asyncio
import logging

from aiogram import Bot
from sqlalchemy import or_, select
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.db.models import Item, Source, User
from app.db.session import SessionLocal
from app.services.collector import apply_fetch
from app.services.digest import build_digest, format_digest, window_start
from app.services.notify import send_html
from app.services.sources import digest_limit, interval_for
from app.utils.time import digest_tz, local_now, utcnow

log = logging.getLogger(__name__)
ERROR_PAUSE_AFTER = 8


async def scheduler_loop(bot: Bot, stop: asyncio.Event) -> None:
    settings = get_settings()
    log.info("scheduler started tick=%ss", settings.collect_tick_seconds)
    while not stop.is_set():
        try:
            await collect_due()
            await send_due_digests(bot)
        except Exception:
            log.exception("scheduler tick")
        try:
            await asyncio.wait_for(stop.wait(), timeout=settings.collect_tick_seconds)
        except TimeoutError:
            pass


async def collect_due() -> None:
    now = utcnow()
    async with SessionLocal() as session:
        result = await session.execute(
            select(Source).where(Source.is_active.is_(True)).options(selectinload(Source.user))
        )
        sources = list(result.scalars())
        for source in sources:
            if source.user and source.user.is_blocked:
                continue
            if source.user:
                source.interval_seconds = interval_for(source.user)
            if source.last_fetched_at and (now - source.last_fetched_at).total_seconds() < source.interval_seconds:
                continue
            try:
                await apply_fetch(session, source)
            except Exception as exc:
                source.last_error = str(exc)[:300]
                source.consecutive_errors += 1
                log.exception("fetch source %s", source.id)
            if source.consecutive_errors >= ERROR_PAUSE_AFTER:
                source.is_active = False
                log.warning("paused source %s after errors", source.id)
        await session.commit()


async def send_due_digests(bot: Bot) -> None:
    now_local = local_now()
    async with SessionLocal() as session:
        result = await session.execute(
            select(User).where(User.digest_enabled.is_(True), User.is_blocked.is_(False))
        )
        users = list(result.scalars())
        for user in users:
            if now_local.hour != user.digest_hour:
                continue
            if user.last_digest_at is not None:
                last_local = user.last_digest_at.astimezone(digest_tz())
                if last_local.date() == now_local.date():
                    continue
            text = await render_user_digest(session, user)
            if text is None:
                continue
            try:
                await send_html(bot, user.telegram_id, text)
                user.last_digest_at = utcnow()
            except Exception:
                log.exception("digest send %s", user.telegram_id)
        await session.commit()


async def render_user_digest(session, user: User, *, allow_empty: bool = False) -> str | None:
    since = window_start()
    result = await session.execute(
        select(Item)
        .join(Source)
        .where(Source.user_id == user.id, Source.is_active.is_(True))
        .where(
            or_(
                Item.published_at >= since,
                (Item.published_at.is_(None)) & (Item.fetched_at >= since),
            )
        )
        .options(selectinload(Item.source))
    )
    items = list(result.scalars().unique())
    digest = build_digest(items, max_items=digest_limit(user))
    if not digest.entries and not allow_empty:
        return None
    return format_digest(digest)
