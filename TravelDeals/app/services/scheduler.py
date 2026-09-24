from __future__ import annotations

import asyncio
import logging

from aiogram import Bot

from app.config import get_settings
from app.db.session import SessionLocal
from app.services.channel import post_deal_photo, send_deal_dm
from app.services.deals import (
    collect_channel_candidates,
    deal_dedupe,
    find_alert_matches,
    is_posted,
    mark_alert_notified,
    mark_posted,
)
from app.services.travelpayouts import get_tp_client

log = logging.getLogger("traveldeals.scheduler")


async def run_deal_tick(bot: Bot) -> int:
    """Fetch deals, post new ones to channel, notify alerts. Returns posts count."""
    settings = get_settings()
    posted = 0
    client = get_tp_client()

    async with SessionLocal() as session:
        candidates = await collect_channel_candidates(client)
        channel_id = settings.channel_chat_id

        for deal in candidates:
            key = deal_dedupe(deal)
            if await is_posted(session, key):
                continue
            ok = False
            if channel_id is not None:
                ok = await post_deal_photo(bot, channel_id, deal)
            await mark_posted(
                session,
                key=key,
                deal_type=getattr(deal, "deal_type", "flight"),
                title=deal.title,
                price=int(deal.price),
                link=str(deal.link),
                to_channel=ok,
            )
            if ok:
                posted += 1

        matches = await find_alert_matches(session, client)
        for alert, flight in matches:
            await send_deal_dm(bot, alert.user.telegram_id, flight)
            await mark_alert_notified(session, alert, flight.price)

        await session.commit()

    log.info("deal tick done, channel posts=%s", posted)
    return posted


async def scheduler_loop(bot: Bot, stop: asyncio.Event) -> None:
    settings = get_settings()
    # small delay after boot
    try:
        await asyncio.wait_for(stop.wait(), timeout=5)
        return
    except asyncio.TimeoutError:
        pass

    while not stop.is_set():
        try:
            await run_deal_tick(bot)
        except Exception:
            log.exception("deal tick error")
        try:
            await asyncio.wait_for(stop.wait(), timeout=settings.deal_tick_seconds)
            break
        except asyncio.TimeoutError:
            continue
