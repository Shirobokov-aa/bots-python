from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

from telethon.tl.custom.message import Message

from app.config import get_settings

log = logging.getLogger("channelmirror.serialize")


async def _download(message: Message, suffix: str) -> str:
    settings = get_settings()
    root = Path(settings.media_dir)
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"{uuid.uuid4().hex}{suffix}"
    await message.download_media(file=str(path))
    return str(path)


def _ext_for(message: Message) -> str:
    if message.photo:
        return ".jpg"
    if message.video or message.video_note:
        return ".mp4"
    if message.animation:
        return ".mp4"
    if message.voice:
        return ".ogg"
    if message.audio:
        name = getattr(message.file, "name", None) if message.file else None
        if name and "." in name:
            return "." + name.rsplit(".", 1)[-1]
        return ".mp3"
    if message.sticker:
        return ".webp"
    if message.document:
        name = getattr(message.file, "name", None) if message.file else None
        if name and "." in name:
            return "." + name.rsplit(".", 1)[-1]
        return ".bin"
    return ".bin"


async def serialize_message(message: Message) -> dict[str, Any]:
    """Build silent-copy payload (no source username / link).

    # TODO(ai): extract entities for better HTML rewrite
    # TODO(ai): detect ad posts by buttons / links
    """
    text = message.message or ""

    if message.poll:
        poll = message.poll
        return {
            "type": "poll",
            "question": poll.question,
            "options": [a.text for a in poll.answers],
            "is_anonymous": True,
            "allows_multiple": bool(getattr(poll, "multiple_choice", False)),
            "text": text,
        }

    if message.grouped_id:
        # Album pieces handled by listener buffer; single piece path:
        media_type = "photo"
        if message.video:
            media_type = "video"
        elif message.document and not message.photo:
            media_type = "document"
        path = await _download(message, _ext_for(message))
        return {
            "type": "album_piece",
            "grouped_id": int(message.grouped_id),
            "media_type": media_type,
            "path": path,
            "text": text,
            "message_id": message.id,
        }

    if message.photo:
        path = await _download(message, ".jpg")
        return {"type": "photo", "path": path, "text": text}

    if message.video:
        path = await _download(message, ".mp4")
        return {"type": "video", "path": path, "text": text}

    if message.video_note:
        path = await _download(message, ".mp4")
        return {"type": "video_note", "path": path, "text": text}

    if message.animation:
        path = await _download(message, ".mp4")
        return {"type": "animation", "path": path, "text": text}

    if message.voice:
        path = await _download(message, ".ogg")
        return {"type": "voice", "path": path, "text": text}

    if message.audio:
        path = await _download(message, _ext_for(message))
        return {"type": "audio", "path": path, "text": text}

    if message.sticker:
        path = await _download(message, ".webp")
        return {"type": "sticker", "path": path, "text": text}

    if message.document:
        path = await _download(message, _ext_for(message))
        name = getattr(message.file, "name", None) if message.file else None
        return {"type": "document", "path": path, "file_name": name, "text": text}

    return {"type": "text", "text": text or "…"}


def merge_album(pieces: list[dict[str, Any]]) -> dict[str, Any]:
    pieces_sorted = sorted(pieces, key=lambda p: p.get("message_id") or 0)
    text = ""
    for p in pieces_sorted:
        if p.get("text"):
            text = p["text"]
            break
    return {
        "type": "album",
        "text": text,
        "items": [
            {"path": p["path"], "media_type": p.get("media_type") or "photo"} for p in pieces_sorted
        ],
    }
