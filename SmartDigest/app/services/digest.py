from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from html import escape

from app.config import get_settings
from app.db.models import Item
from app.utils.text import canonicalize_url, normalize_title
from app.utils.time import local_now, utcnow


@dataclass
class DigestEntry:
    title: str
    url: str | None
    source_title: str
    summary: str | None


@dataclass
class Digest:
    entries: list[DigestEntry]
    sources_count: int
    skipped_noise: int
    skipped_dupes: int
    window_hours: int
    truncated: int = 0


def build_digest(items: list[Item], *, max_items: int, window_hours: int | None = None) -> Digest:
    settings = get_settings()
    window = window_hours or settings.digest_window_hours
    seen_hash: set[str] = set()
    seen_title: set[str] = set()
    seen_url: set[str] = set()
    skipped_noise = 0
    skipped_dupes = 0
    picked: list[DigestEntry] = []
    source_ids: set[int] = set()

    ordered = sorted(items, key=_item_time, reverse=True)
    leftover = 0
    for item in ordered:
        if item.is_noise:
            skipped_noise += 1
            continue
        title_key = normalize_title(item.title)
        url_key = canonicalize_url(item.url)
        if item.content_hash in seen_hash or (title_key and title_key in seen_title) or (url_key and url_key in seen_url):
            skipped_dupes += 1
            continue
        if len(picked) >= max_items:
            leftover += 1
            continue
        seen_hash.add(item.content_hash)
        if title_key:
            seen_title.add(title_key)
        if url_key:
            seen_url.add(url_key)
        source_title = item.source.title if item.source else "источник"
        picked.append(
            DigestEntry(
                title=item.title,
                url=item.url,
                source_title=source_title or "источник",
                summary=item.summary,
            )
        )
        source_ids.add(item.source_id)
    return Digest(
        entries=picked,
        sources_count=len(source_ids),
        skipped_noise=skipped_noise,
        skipped_dupes=skipped_dupes,
        window_hours=window,
        truncated=max(0, leftover),
    )


def format_digest(digest: Digest) -> str:
    now = local_now()
    months = (
        "",
        "января",
        "февраля",
        "марта",
        "апреля",
        "мая",
        "июня",
        "июля",
        "августа",
        "сентября",
        "октября",
        "ноября",
        "декабря",
    )
    stamp = f"{now.day} {months[now.month]}"
    if not digest.entries:
        return (
            f"📰 <b>SmartDigest</b> · {stamp}\n\n"
            f"За последние {digest.window_hours} ч. ничего нового.\n"
            "Пришли RSS, сайт или @канал — соберу ленту."
        )

    lines = [f"📰 <b>SmartDigest</b> · {stamp}", ""]
    for index, entry in enumerate(digest.entries, start=1):
        title = escape(entry.title)
        source = escape(entry.source_title)
        if entry.url:
            lines.append(f"{index}. <b>{title}</b>\n{source} · <a href=\"{escape(entry.url)}\">читать</a>")
        else:
            lines.append(f"{index}. <b>{title}</b>\n{source}")
        if entry.summary and entry.summary.strip() != entry.title.strip():
            lines.append(f"<i>{escape(entry.summary)}</i>")
        lines.append("")

    footer = (
        f"{len(digest.entries)} материалов из {digest.sources_count} лент. "
        f"Отсеяно: {digest.skipped_dupes} повтор., {digest.skipped_noise} реклама."
    )
    if digest.truncated:
        footer += f" Ещё {digest.truncated} не влезли."
    lines.append(f"<i>{footer}</i>")
    lines.append("ИИ-саммари подключим позже.")
    return "\n".join(lines).strip()


def empty_sources_text() -> str:
    return "Пока нет источников. Пришли RSS, ссылку на сайт или @канал."


def _item_time(item: Item):
    return item.published_at or item.fetched_at


def window_start():
    return utcnow() - timedelta(hours=get_settings().digest_window_hours)
