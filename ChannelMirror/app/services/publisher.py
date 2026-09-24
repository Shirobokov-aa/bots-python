from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from aiogram.types import (
    BufferedInputFile,
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
)

log = logging.getLogger("channelmirror.publisher")


def _file(path: str, name: str | None = None) -> BufferedInputFile:
    data = Path(path).read_bytes()
    return BufferedInputFile(data, filename=name or Path(path).name)


async def publish_silent(bot: Bot, chat_id: int, payload: dict[str, Any]) -> None:
    """Post content as original (no forward / no source link header).

    # TODO(ai): transform_payload already applied upstream; optional second pass here
    """
    kind = payload.get("type") or "text"
    text = payload.get("text") or ""
    # Never attach source attribution in MVP (user request: без ссылок на источники)
    # TODO(ai): optional "via @source" footer toggle

    if kind == "text":
        await bot.send_message(chat_id, text or "…", disable_web_page_preview=False)
        return

    if kind == "photo":
        await bot.send_photo(chat_id, _file(payload["path"]), caption=text or None)
        return

    if kind == "video":
        await bot.send_video(chat_id, _file(payload["path"]), caption=text or None)
        return

    if kind == "document":
        await bot.send_document(
            chat_id,
            _file(payload["path"], payload.get("file_name")),
            caption=text or None,
        )
        return

    if kind == "audio":
        await bot.send_audio(chat_id, _file(payload["path"]), caption=text or None)
        return

    if kind == "voice":
        await bot.send_voice(chat_id, _file(payload["path"]), caption=text or None)
        return

    if kind == "animation":
        await bot.send_animation(chat_id, _file(payload["path"]), caption=text or None)
        return

    if kind == "sticker":
        await bot.send_sticker(chat_id, _file(payload["path"], "sticker.webp"))
        return

    if kind == "video_note":
        await bot.send_video_note(chat_id, _file(payload["path"]))
        return

    if kind == "album":
        media_items = payload.get("items") or []
        group: list[Any] = []
        for i, item in enumerate(media_items):
            path = item["path"]
            caption = text if i == 0 else None
            mtype = item.get("media_type") or "photo"
            if mtype == "video":
                group.append(InputMediaVideo(media=_file(path), caption=caption))
            elif mtype == "document":
                group.append(InputMediaDocument(media=_file(path), caption=caption))
            elif mtype == "audio":
                group.append(InputMediaAudio(media=_file(path), caption=caption))
            else:
                group.append(InputMediaPhoto(media=_file(path), caption=caption))
        if group:
            await bot.send_media_group(chat_id, media=group)
        return

    if kind == "poll":
        await bot.send_poll(
            chat_id,
            question=payload["question"],
            options=payload["options"],
            is_anonymous=payload.get("is_anonymous", True),
            allows_multiple_answers=payload.get("allows_multiple", False),
        )
        return

    # Fallback: text dump
    log.warning("unknown payload type %s, fallback text", kind)
    await bot.send_message(chat_id, text or json.dumps(payload, ensure_ascii=False)[:3500])


async def safe_publish(bot: Bot, chat_id: int, payload: dict[str, Any]) -> str | None:
    """Return error string or None on success."""
    try:
        await publish_silent(bot, chat_id, payload)
        return None
    except TelegramAPIError as exc:
        log.error("publish fail chat=%s: %s", chat_id, exc)
        return str(exc)
    except OSError as exc:
        log.error("media read fail: %s", exc)
        return str(exc)
