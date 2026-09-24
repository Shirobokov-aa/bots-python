from __future__ import annotations

from datetime import datetime

from bs4 import BeautifulSoup

from app.ingest.types import FetchedItem, FetchResult
from app.utils.text import snippet, strip_html


def parse_telegram_html(html: str, fetch_url: str) -> FetchResult:
    soup = BeautifulSoup(html, "lxml")
    channel = soup.select_one(".tgme_channel_info_header_title")
    title = strip_html(channel.get_text(" ", strip=True) if channel else "") or None
    items: list[FetchedItem] = []
    for node in soup.select(".tgme_widget_message"):
        post_id = (node.get("data-post") or "").strip()
        date_link = node.select_one("a.tgme_widget_message_date")
        href = (date_link.get("href") if date_link else "") or ""
        if href.startswith("https://t.me/"):
            href = href.split("?")[0]
        text_node = node.select_one(".tgme_widget_message_text")
        text = strip_html(text_node.decode_contents() if text_node else "")
        if not text:
            continue
        title_line = text.split("\n", 1)[0][:512]
        time_node = date_link.select_one("time") if date_link else None
        published = None
        stamp = time_node.get("datetime") if time_node else None
        if stamp:
            published = _parse_iso(stamp)
        external = post_id or href or title_line
        items.append(
            FetchedItem(
                external_id=external[:512],
                title=title_line,
                url=href or None,
                summary=snippet(text) or None,
                published_at=published,
            )
        )
    if not items and "tgme_channel_info" not in html and "tgme_widget_message" not in html:
        return FetchResult(error="канал недоступен или приватный")
    return FetchResult(title=title, items=items, canonical_url=fetch_url, kind="telegram")


def _parse_iso(value: str) -> datetime | None:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
