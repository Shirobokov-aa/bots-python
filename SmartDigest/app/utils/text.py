from __future__ import annotations

import hashlib
import re
from html import unescape
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from bs4 import BeautifulSoup

TRACKING_PARAMS = {
    "utm_source",
    "utm_medium",
    "utm_campaign",
    "utm_term",
    "utm_content",
    "utm_id",
    "fbclid",
    "gclid",
    "ysclid",
    "yclid",
    "mc_cid",
    "mc_eid",
    "igshid",
    "si",
}

NOISE_MARKERS = (
    "erid",
    "#реклама",
    "рекламная интеграция",
    "партнёрский материал",
    "партнерский материал",
    "на правах рекламы",
    "промокод",
    "sponsored",
    "#ad",
    "giveaway",
    "только сегодня скидка",
    "подписывайся на канал",
    "подпишись на канал",
)

_PUNCT_RE = re.compile(r"[^\w\s]+", re.UNICODE)
_SPACE_RE = re.compile(r"\s+")
_TAG_RE = re.compile(r"<[^>]+>")


def strip_html(value: str | None) -> str:
    if not value:
        return ""
    if "<" not in value and "&" not in value:
        return _SPACE_RE.sub(" ", unescape(value)).strip()
    text = BeautifulSoup(value, "lxml").get_text(" ", strip=True)
    if not text:
        text = unescape(_TAG_RE.sub(" ", value))
    return _SPACE_RE.sub(" ", text).strip()


def snippet(value: str | None, limit: int = 180) -> str:
    text = strip_html(value)
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0]
    return (cut or text[: limit - 1]).rstrip(".,;:") + "…"


def normalize_title(value: str | None) -> str:
    text = strip_html(value).lower()
    text = _PUNCT_RE.sub(" ", text)
    return _SPACE_RE.sub(" ", text).strip()


def canonicalize_url(url: str | None) -> str:
    if not url:
        return ""
    parts = urlsplit(url.strip())
    query = [
        (key, val)
        for key, val in parse_qsl(parts.query, keep_blank_values=True)
        if key.lower() not in TRACKING_PARAMS
    ]
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, urlencode(query), ""))


def content_hash(title: str | None, url: str | None) -> str:
    payload = f"{normalize_title(title)}|{canonicalize_url(url)}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def looks_like_noise(title: str | None, summary: str | None = None) -> bool:
    blob = f"{title or ''} {summary or ''}".lower()
    return any(marker in blob for marker in NOISE_MARKERS)


def split_telegram(text: str, limit: int = 3500) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    rest = text
    while rest:
        if len(rest) <= limit:
            chunks.append(rest)
            break
        window = rest[:limit]
        split_at = window.rfind("\n\n")
        if split_at < limit // 3:
            split_at = window.rfind("\n")
        if split_at < limit // 3:
            split_at = limit
        chunks.append(rest[:split_at].rstrip())
        rest = rest[split_at:].lstrip()
    return chunks
