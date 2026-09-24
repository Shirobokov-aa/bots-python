from __future__ import annotations

import httpx

from app.config import get_settings

_client: httpx.AsyncClient | None = None


def _headers() -> dict[str, str]:
    settings = get_settings()
    return {
        "User-Agent": settings.user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml,application/rss+xml,application/atom+xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        "Cache-Control": "no-cache",
    }


async def get_http_client() -> httpx.AsyncClient:
    global _client
    if _client is None or _client.is_closed:
        settings = get_settings()
        kwargs: dict = {
            "headers": _headers(),
            "timeout": settings.http_timeout,
            "follow_redirects": True,
        }
        if settings.http_proxy:
            kwargs["proxy"] = settings.http_proxy
        _client = httpx.AsyncClient(**kwargs)
    return _client


async def close_http_client() -> None:
    global _client
    if _client is not None and not _client.is_closed:
        await _client.aclose()
    _client = None
