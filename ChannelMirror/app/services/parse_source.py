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


@dataclass
class ParsedInvite:
    """Private invite: t.me/+HASH or t.me/joinchat/HASH."""

    hash: str
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


def parse_invite(text: str) -> ParsedInvite | None:
    candidate = extract_candidate(text)
    if not candidate:
        raw = (text or "").strip().split()[0] if (text or "").strip() else ""
        if raw.startswith("+") and len(raw) > 2:
            h = raw[1:]
            return ParsedInvite(hash=h, display=f"t.me/+{h}", url=f"https://t.me/+{h}")
        return None
    if not candidate.startswith("http"):
        if candidate.startswith("t.me/") or candidate.startswith("telegram.me/"):
            candidate = "https://" + candidate
        else:
            return None
    host = urlsplit(candidate).netloc.lower()
    if host not in TG_HOSTS:
        return None
    parts = [p for p in urlsplit(candidate).path.split("/") if p]
    if not parts:
        return None
    if parts[0].startswith("+") and len(parts[0]) > 1:
        h = parts[0][1:]
        return ParsedInvite(hash=h, display=f"t.me/+{h}", url=f"https://t.me/+{h}")
    if parts[0] == "joinchat" and len(parts) >= 2:
        h = parts[1]
        return ParsedInvite(hash=h, display=f"t.me/joinchat/{h}", url=f"https://t.me/joinchat/{h}")
    return None


def private_source_slug(chat_id: int) -> str:
    """Internal username for sources without public @."""
    return f"id{abs(int(chat_id))}"


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
