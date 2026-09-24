from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from time import struct_time

import feedparser

from app.ingest.types import FetchedItem, FetchResult
from app.utils.text import snippet, strip_html


def parse_feed(body: bytes, url: str) -> FetchResult:
    parsed = feedparser.parse(body)
    if parsed.bozo and not parsed.entries and not parsed.feed:
        error = getattr(parsed, "bozo_exception", None)
        return FetchResult(error=str(error)[:200] if error else "не похоже на RSS/Atom")

    title = strip_html(parsed.feed.get("title")) or None
    items: list[FetchedItem] = []
    for entry in parsed.entries:
        entry_title = strip_html(entry.get("title"))
        if not entry_title:
            continue
        link = (entry.get("link") or "").strip() or None
        external = str(entry.get("id") or link or entry_title)[:512]
        summary_src = entry.get("summary") or entry.get("description") or ""
        if entry.get("content"):
            summary_src = entry.content[0].get("value") or summary_src
        items.append(
            FetchedItem(
                external_id=external,
                title=entry_title[:512],
                url=link,
                summary=snippet(summary_src) or None,
                published_at=_entry_time(entry),
            )
        )
    if not items and not title:
        return FetchResult(error="лента пустая или не распознана")
    return FetchResult(title=title, items=items, canonical_url=url, kind="rss")


def _entry_time(entry) -> datetime | None:
    for key in ("published_parsed", "updated_parsed"):
        parsed: struct_time | None = entry.get(key)
        if parsed:
            return datetime(*parsed[:6], tzinfo=timezone.utc)
    return None


async def parse_feed_async(body: bytes, url: str) -> FetchResult:
    return await asyncio.to_thread(parse_feed, body, url)
