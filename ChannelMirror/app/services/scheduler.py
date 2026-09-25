from __future__ import annotations

import asyncio
import json
import logging

from aiogram import Bot

from app.config import get_settings
from app.db.session import SessionLocal
from app.services.queue import destinations_due, mark_failed, mark_posted, next_pending_for_destination
from app.services.publisher import safe_publish
from app.services.source_label import apply_source_label_to_payload, source_display_name

log = logging.getLogger("channelmirror.scheduler")


async def publish_tick(bot: Bot) -> int:
    """Publish at most one pending item per due destination.

    Spacing = route.interval_seconds (default 1–2h). Silent copy;
    optional plain-text source label per route.
    """
    posted = 0
    async with SessionLocal() as session:
        due = await destinations_due(session)
        for dest in due:
            item = await next_pending_for_destination(session, dest.id)
            if item is None:
                continue
            payload = json.loads(item.payload_json)
            route = item.route
            if route is not None and route.show_source_label:
                name = source_display_name(route.source)
                payload = apply_source_label_to_payload(payload, name)
            err = await safe_publish(bot, dest.chat_id, payload)
            if err:
                await mark_failed(session, item, err)
            else:
                await mark_posted(session, item, dest)
                posted += 1
        await session.commit()
    if posted:
        log.info("publish tick posted=%s", posted)
    return posted


async def scheduler_loop(bot: Bot, stop: asyncio.Event) -> None:
    settings = get_settings()
    try:
        await asyncio.wait_for(stop.wait(), timeout=3)
        return
    except asyncio.TimeoutError:
        pass

    while not stop.is_set():
        try:
            await publish_tick(bot)
        except Exception:
            log.exception("publish tick error")
        try:
            await asyncio.wait_for(stop.wait(), timeout=settings.publish_tick_seconds)
            break
        except asyncio.TimeoutError:
            continue
