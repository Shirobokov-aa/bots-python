from __future__ import annotations

from typing import Any

from app.db.models import Source

# Plain text only — never @username / t.me (Telegram would make them clickable).
FOOTER_TEMPLATE = 'Источник: "{name}"'
TEXT_LIMIT = 4096
CAPTION_LIMIT = 1024


def source_display_name(source: Source | None) -> str | None:
    """Human channel title for attribution. No links, no @mention."""
    if source is None:
        return None
    title = (source.title or "").strip()
    if title:
        return title
    uname = (source.username or "").strip().lstrip("@")
    if uname and not uname.startswith("id"):
        # Without @ so Telegram does not auto-link a mention.
        return uname
    return None


def format_source_footer(name: str) -> str:
    return FOOTER_TEMPLATE.format(name=name)


def append_source_footer(text: str | None, name: str, limit: int = TEXT_LIMIT) -> str:
    footer = format_source_footer(name)
    body = (text or "").rstrip()
    if not body or body == "…":
        return footer[:limit]
    joined = f"{body}\n\n{footer}"
    if len(joined) <= limit:
        return joined
    room = limit - len(footer) - 2
    if room <= 0:
        return footer[:limit]
    return f"{body[:room].rstrip()}\n\n{footer}"


def apply_source_label_to_payload(payload: dict[str, Any], name: str | None) -> dict[str, Any]:
    """Return a copy of payload with plain-text source footer in text/caption."""
    if not name:
        return payload
    out = dict(payload)
    kind = out.get("type") or "text"
    # Types without caption: follow-up message after the media/poll.
    if kind in {"sticker", "video_note", "poll"}:
        out["_source_followup"] = format_source_footer(name)
        return out
    limit = TEXT_LIMIT if kind == "text" else CAPTION_LIMIT
    out["text"] = append_source_footer(out.get("text"), name, limit=limit)
    return out
