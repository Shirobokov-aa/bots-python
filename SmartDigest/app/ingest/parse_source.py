from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlsplit

URL_RE = re.compile(r"https?://[^\s<>()]+", re.IGNORECASE)
TG_AT_RE = re.compile(r"^@([A-Za-z0-9_]{4,32})$")
TG_HOSTS = {"t.me", "telegram.me", "www.t.me", "www.telegram.me"}
RESERVED_TG = {
    "share",
    "socks",
    "proxy",
    "addstickers",
    "joinchat",
    "iv",
    "login",
    "setlanguage",
    "addlist",
    "boost",
}

FEED_NAMES = {
    "rss",
    "feed",
    "atom",
    "rss.xml",
    "atom.xml",
    "feed.xml",
    "index.xml",
    "rss2.xml",
}


@dataclass
class ParsedSource:
    kind: str
    url: str
    display: str
    username: str | None = None


def extract_candidate(text: str) -> str | None:
    raw = (text or "").strip()
    if not raw:
        return None
    first = raw.split()[0]
    if TG_AT_RE.match(first):
        return first
    match = URL_RE.search(raw)
    if match:
        return match.group(0).rstrip(").,;!?»\"'")
    at = re.search(r"@([A-Za-z0-9_]{4,32})\b", raw)
    if at:
        return at.group(0)
    if first.startswith("t.me/") or first.startswith("telegram.me/"):
        return "https://" + first.rstrip(").,;!?»\"'")
    return None


def parse_source(text: str) -> ParsedSource | None:
    candidate = extract_candidate(text)
    if not candidate:
        return None
    at = TG_AT_RE.match(candidate)
    if at:
        username = at.group(1)
        return ParsedSource(
            kind="telegram",
            url=f"https://t.me/s/{username}",
            display=f"@{username}",
            username=username,
        )
    if not candidate.startswith("http"):
        return None
    host = urlsplit(candidate).netloc.lower()
    if host in TG_HOSTS:
        username = _telegram_username(candidate)
        if not username:
            return None
        return ParsedSource(
            kind="telegram",
            url=f"https://t.me/s/{username}",
            display=f"@{username}",
            username=username,
        )
    if _looks_like_feed_url(candidate):
        return ParsedSource(kind="rss", url=candidate, display=candidate)
    return ParsedSource(kind="website", url=candidate, display=candidate)


def _looks_like_feed_url(url: str) -> bool:
    path = urlsplit(url).path.lower().rstrip("/")
    if "sitemap" in path:
        return False
    name = path.rsplit("/", 1)[-1]
    if name in FEED_NAMES:
        return True
    if path.endswith((".rss", ".atom")):
        return True
    wrapped = f"/{path.strip('/')}/"
    if any(token in wrapped for token in ("/rss/", "/feed/", "/feeds/", "/atom/")):
        return True
    return path.endswith(("/rss", "/feed", "/atom"))


def _telegram_username(url: str) -> str | None:
    parts = [p for p in urlsplit(url).path.split("/") if p]
    if not parts:
        return None
    if parts[0].startswith("+") or parts[0] in {"joinchat"}:
        return None
    if parts[0] == "s" and len(parts) >= 2:
        username = parts[1]
    else:
        username = parts[0]
    if username.lower() in RESERVED_TG:
        return None
    if not re.fullmatch(r"[A-Za-z0-9_]{4,32}", username):
        return None
    return username


def absolutize(base: str, href: str) -> str:
    return urljoin(base, href)
