from __future__ import annotations

import httpx

from app.ingest.client import close_http_client, get_http_client
from app.ingest.parse_source import ParsedSource
from app.ingest.rss import parse_feed_async
from app.ingest.telegram import parse_telegram_html
from app.ingest.types import FetchResult
from app.ingest.website import discover_feed_urls, looks_like_feed

__all__ = ["FetchResult", "close_http_client", "fetch_parsed", "fetch_url"]


async def fetch_parsed(parsed: ParsedSource) -> FetchResult:
    if parsed.kind == "telegram":
        return await _fetch_telegram(parsed.url)
    if parsed.kind == "rss":
        return await _fetch_rss(parsed.url)
    return await _fetch_website(parsed.url)


async def fetch_url(kind: str, url: str) -> FetchResult:
    if kind == "telegram":
        return await _fetch_telegram(url)
    if kind == "rss":
        return await _fetch_rss(url)
    return await _fetch_website(url)


async def _get(url: str) -> httpx.Response:
    client = await get_http_client()
    return await client.get(url)


async def _fetch_rss(url: str) -> FetchResult:
    try:
        response = await _get(url)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        return FetchResult(error=str(exc)[:200])
    result = await parse_feed_async(response.content, str(response.url))
    result.canonical_url = str(response.url)
    result.kind = "rss"
    return result


async def _fetch_telegram(url: str) -> FetchResult:
    try:
        response = await _get(url)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        return FetchResult(error=str(exc)[:200])
    return parse_telegram_html(response.text, str(response.url))


async def _fetch_website(url: str) -> FetchResult:
    try:
        response = await _get(url)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        return FetchResult(error=str(exc)[:200])

    if looks_like_feed(response.headers.get("content-type"), response.content):
        result = await parse_feed_async(response.content, str(response.url))
        result.canonical_url = str(response.url)
        result.kind = "rss"
        return result

    candidates = discover_feed_urls(response.text, str(response.url))
    last_error = "RSS на сайте не найден — пришли прямую ссылку на ленту"
    for candidate in candidates[:8]:
        result = await _fetch_rss(candidate)
        if result.error:
            last_error = result.error
            continue
        if result.items:
            result.kind = "rss"
            return result
    return FetchResult(error=last_error, kind="website")
