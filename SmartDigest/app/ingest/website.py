from __future__ import annotations

from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

RSS_TYPES = {
    "application/rss+xml",
    "application/atom+xml",
    "application/xml",
    "text/xml",
}

COMMON_FEED_PATHS = (
    "/feed",
    "/rss",
    "/rss.xml",
    "/atom.xml",
    "/feed.xml",
    "/index.xml",
    "/feeds/posts/default",
)


def looks_like_feed(content_type: str | None, body: bytes) -> bool:
    ctype = (content_type or "").split(";")[0].strip().lower()
    if ctype in RSS_TYPES or ctype.endswith("+xml"):
        if b"<rss" in body[:4000] or b"<feed" in body[:4000] or b"<rdf:RDF" in body[:4000]:
            return True
    head = body[:2000].lstrip().lower()
    return head.startswith(b"<?xml") and (b"<rss" in head or b"<feed" in head or b"<rdf:rdf" in head)


def discover_feed_urls(html: str, page_url: str) -> list[str]:
    soup = BeautifulSoup(html, "lxml")
    found: list[str] = []
    seen: set[str] = set()
    for link in soup.select("link[rel~=alternate]"):
        href = (link.get("href") or "").strip()
        if not href:
            continue
        type_ = (link.get("type") or "").lower()
        if "rss" in type_ or "atom" in type_ or "xml" in type_:
            abs_url = urljoin(page_url, href)
            if abs_url not in seen:
                seen.add(abs_url)
                found.append(abs_url)
    origin = f"{urlsplit(page_url).scheme}://{urlsplit(page_url).netloc}"
    for path in COMMON_FEED_PATHS:
        candidate = origin + path
        if candidate not in seen:
            seen.add(candidate)
            found.append(candidate)
    return found
