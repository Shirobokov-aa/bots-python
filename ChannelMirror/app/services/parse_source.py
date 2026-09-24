from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urlsplit

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
    "c",
}


@dataclass
class ParsedChannel:
    username: str
    display: str
    url: str


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


def parse_channel(text: str) -> ParsedChannel | None:
    candidate = extract_candidate(text)
    if not candidate:
        return None
    at = TG_AT_RE.match(candidate)
    if at:
        username = at.group(1)
        return ParsedChannel(
            username=username.lower(),
            display=f"@{username}",
            url=f"https://t.me/{username}",
        )
    if not candidate.startswith("http"):
        return None
    host = urlsplit(candidate).netloc.lower()
    if host not in TG_HOSTS:
        return None
    username = _telegram_username(candidate)
    if not username:
        return None
    return ParsedChannel(
        username=username.lower(),
        display=f"@{username}",
        url=f"https://t.me/{username}",
    )


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
