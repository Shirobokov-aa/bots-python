from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from typing import Any

from telethon import TelegramClient, events, utils
from telethon.errors import UserAlreadyParticipantError
from telethon.sessions import StringSession
from telethon.tl.functions.channels import JoinChannelRequest
from telethon.tl.functions.messages import CheckChatInviteRequest, ImportChatInviteRequest
from telethon.tl.types import ChatInviteAlready

from app.config import get_settings
from app.db.session import SessionLocal
from app.services.queue import enqueue_for_routes, mark_seen
from app.services.routes import (
    active_sources,
    routes_for_chat_id,
    routes_for_username,
)
from app.services.serialize import merge_album, serialize_message

log = logging.getLogger("channelmirror.telethon")


class SourceListener:
    """Telethon reader for source channels the user-session can see."""

    def __init__(self) -> None:
        self._client: TelegramClient | None = None
        self._task: asyncio.Task | None = None
        self._album_buf: dict[int, list[dict[str, Any]]] = defaultdict(list)
        self._album_tasks: dict[int, asyncio.Task] = {}
        self._watched_usernames: set[str] = set()
        self._watched_chat_ids: set[int] = set()

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
            sources = await active_sources(session)
            if self._client:
                for src in sources:
                    await self._ensure_joined(session, src)
            self._watched_usernames = {
                s.username.lower()
                for s in sources
                if s.username and not str(s.username).startswith("id")
            }
            self._watched_chat_ids = {int(s.chat_id) for s in sources if s.chat_id is not None}
            await session.commit()
        log.info(
            "watchlist usernames=%s chat_ids=%s",
            sorted(self._watched_usernames),
            sorted(self._watched_chat_ids),
        )

    async def resolve_chat(self, chat_id: int) -> tuple[int, str | None, str | None] | None:
        """Return (peer_id, title, username) if Telethon account can see the chat."""
        if not self._client:
            return None
        try:
            entity = await self._client.get_entity(chat_id)
        except Exception as exc:
            log.warning("resolve chat_id=%s failed: %s", chat_id, exc)
            return None
        peer_id = utils.get_peer_id(entity)
        title = getattr(entity, "title", None)
        uname = getattr(entity, "username", None)
        return peer_id, title, uname.lower() if uname else None

    async def join_invite(self, invite_hash: str) -> tuple[int, str | None, str | None]:
        """Join private invite; return (peer_id, title, username). Raises on failure."""
        if not self._client:
            raise RuntimeError("Telethon offline")
        invite = await self._client(CheckChatInviteRequest(invite_hash))
        entity = None
        if isinstance(invite, ChatInviteAlready):
            entity = invite.chat
        else:
            # ChatInvite / ChatInvitePeek — join
            updates = await self._client(ImportChatInviteRequest(invite_hash))
            chats = getattr(updates, "chats", None) or []
            if not chats:
                raise RuntimeError("invite joined but no chat in response")
            entity = chats[0]
        peer_id = utils.get_peer_id(entity)
        title = getattr(entity, "title", None)
        uname = getattr(entity, "username", None)
        log.info("invite ok chat_id=%s title=%r", peer_id, title)
        return peer_id, title, uname.lower() if uname else None

    async def _ensure_joined(self, session, src) -> None:
        assert self._client is not None
        entity = None
        if src.chat_id is not None:
            try:
                entity = await self._client.get_entity(int(src.chat_id))
            except Exception as exc:
                log.warning("resolve chat_id=%s (@%s) failed: %s", src.chat_id, src.username, exc)
        if entity is None and src.username and not str(src.username).startswith("id"):
            try:
                entity = await self._client.get_entity(src.username)
            except Exception as exc:
                log.warning("resolve @%s failed: %s", src.username, exc)
                return
        if entity is None:
            return
        peer_id = utils.get_peer_id(entity)
        title = getattr(entity, "title", None)
        public_uname = getattr(entity, "username", None)
        changed = False
        if src.chat_id != peer_id:
            src.chat_id = peer_id
            changed = True
        if title and src.title != title:
            src.title = title
            changed = True
        if public_uname and src.username != public_uname.lower():
            src.username = public_uname.lower()
            changed = True
        if changed:
            await session.flush()
        if public_uname or not str(src.username).startswith("id"):
            try:
                await self._client(JoinChannelRequest(entity))
                log.info("joined source @%s chat_id=%s", src.username, peer_id)
            except UserAlreadyParticipantError:
                pass
            except Exception as exc:
                log.warning("join @%s failed: %s", src.username, exc)
        else:
            log.info("private source ok chat_id=%s title=%r", peer_id, title)

    async def _handle(self, event: events.NewMessage.Event) -> None:
        chat_id = event.chat_id
        chat = await event.get_chat()
        username = (getattr(chat, "username", None) or "").lower()

        by_id = chat_id is not None and int(chat_id) in self._watched_chat_ids
        by_name = bool(username) and username in self._watched_usernames
        if not by_id and not by_name:
            return

        message = event.message
        async with SessionLocal() as session:
            routes = []
            if by_id:
                routes = await routes_for_chat_id(session, int(chat_id))
            if not routes and by_name:
                routes = await routes_for_username(session, username)
            if not routes:
                await session.commit()
                return
            source_id = routes[0].source_id
            label = username or str(chat_id)
            fresh = await mark_seen(session, source_id, message.id, message.grouped_id)
            if not fresh:
                await session.commit()
                return

            payload = await serialize_message(message)

            if payload.get("type") == "album_piece":
                gid = int(payload["grouped_id"])
                payload["_routes"] = [r.id for r in routes]
                payload["_source_id"] = source_id
                payload["_username"] = username
                payload["_chat_id"] = chat_id
                self._album_buf[gid].append(payload)
                if gid in self._album_tasks:
                    self._album_tasks[gid].cancel()
                self._album_tasks[gid] = asyncio.create_task(self._flush_album(gid))
                await session.commit()
                return

            n = await enqueue_for_routes(session, routes, message.id, payload)
            await session.commit()
            log.info("enqueued %s from %s msg=%s", n, label, message.id)

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
        chat_id = pieces[0].get("_chat_id")
        album = merge_album(pieces)
        first_msg_id = min(p.get("message_id") or 0 for p in pieces)
        async with SessionLocal() as session:
            routes = []
            if chat_id is not None:
                routes = await routes_for_chat_id(session, int(chat_id))
            if not routes and username:
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
