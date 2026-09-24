from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any

from telethon import TelegramClient, events
from telethon.sessions import StringSession

from app.config import get_settings
from app.db.session import SessionLocal
from app.services.queue import enqueue_for_routes, mark_seen
from app.services.routes import active_source_usernames, routes_for_username
from app.services.serialize import merge_album, serialize_message

log = logging.getLogger("channelmirror.telethon")


class SourceListener:
    """Telethon reader for public source channels.

    # TODO(ai): pass raw text into filter before download to save bandwidth
    """

    def __init__(self) -> None:
        self._client: TelegramClient | None = None
        self._task: asyncio.Task | None = None
        self._album_buf: dict[int, list[dict[str, Any]]] = defaultdict(list)
        self._album_tasks: dict[int, asyncio.Task] = {}
        self._watched: set[str] = set()

    @property
    def client(self) -> TelegramClient | None:
        return self._client

    async def start(self) -> None:
        settings = get_settings()
        if not settings.telethon_ready:
            log.warning("Telethon off: set TELEGRAM_API_ID/HASH/SESSION")
            return
        self._client = TelegramClient(
            StringSession(settings.telegram_session),
            settings.telegram_api_id,
            settings.telegram_api_hash,
        )
        await self._client.connect()
        if not await self._client.is_user_authorized():
            log.error("Telethon session not authorized — run scripts/telethon_login.py")
            await self._client.disconnect()
            self._client = None
            return

        @self._client.on(events.NewMessage())
        async def _on_new(event: events.NewMessage.Event) -> None:
            await self._handle(event)

        self._task = asyncio.create_task(self._client.run_until_disconnected(), name="telethon")
        await self.refresh_watchlist()
        log.info("Telethon listener on")

    async def stop(self) -> None:
        for task in list(self._album_tasks.values()):
            task.cancel()
        if self._client:
            await self._client.disconnect()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self._client = None

    async def refresh_watchlist(self) -> None:
        async with SessionLocal() as session:
            self._watched = await active_source_usernames(session)
            await session.commit()
        log.info("watchlist: %s", sorted(self._watched))

    async def _handle(self, event: events.NewMessage.Event) -> None:
        chat = await event.get_chat()
        username = (getattr(chat, "username", None) or "").lower()
        if not username or username not in self._watched:
            return

        message = event.message
        async with SessionLocal() as session:
            routes = await routes_for_username(session, username)
            if not routes:
                await session.commit()
                return
            source_id = routes[0].source_id
            fresh = await mark_seen(session, source_id, message.id, message.grouped_id)
            if not fresh:
                await session.commit()
                return

            payload = await serialize_message(message)

            if payload.get("type") == "album_piece":
                gid = int(payload["grouped_id"])
                # stash route ids + source msg for flush
                payload["_routes"] = [r.id for r in routes]
                payload["_source_id"] = source_id
                payload["_username"] = username
                self._album_buf[gid].append(payload)
                if gid in self._album_tasks:
                    self._album_tasks[gid].cancel()
                self._album_tasks[gid] = asyncio.create_task(self._flush_album(gid))
                await session.commit()
                return

            # # TODO(ai): should_publish / transform inside enqueue_for_routes
            n = await enqueue_for_routes(session, routes, message.id, payload)
            await session.commit()
            log.info("enqueued %s from @%s msg=%s", n, username, message.id)

    async def _flush_album(self, grouped_id: int) -> None:
        try:
            await asyncio.sleep(get_settings().album_wait_seconds)
        except asyncio.CancelledError:
            return
        pieces = self._album_buf.pop(grouped_id, [])
        self._album_tasks.pop(grouped_id, None)
        if not pieces:
            return
        username = pieces[0].get("_username") or ""
        album = merge_album(pieces)
        first_msg_id = min(p.get("message_id") or 0 for p in pieces)
        async with SessionLocal() as session:
            routes = await routes_for_username(session, username)
            n = await enqueue_for_routes(session, routes, first_msg_id, album)
            await session.commit()
        log.info("enqueued album %s pieces=%s routes=%s", grouped_id, len(pieces), n)


_listener: SourceListener | None = None


def get_listener() -> SourceListener:
    global _listener
    if _listener is None:
        _listener = SourceListener()
    return _listener
