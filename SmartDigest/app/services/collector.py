from __future__ import annotations

from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Item, Source
from app.ingest import fetch_url
from app.ingest.types import FetchResult
from app.utils.text import content_hash, looks_like_noise, snippet
from app.utils.time import utcnow


async def persist_fetch(session: AsyncSession, source: Source, result: FetchResult) -> int:
    source.last_fetched_at = utcnow()
    if result.error and not result.items:
        source.consecutive_errors += 1
        source.last_error = result.error[:300]
        return 0

    source.last_error = None
    source.consecutive_errors = 0
    if result.title:
        source.title = result.title[:512]
    if result.kind:
        source.kind = result.kind
    if result.canonical_url and result.kind == "rss":
        source.url = result.canonical_url

    now = utcnow()
    added = 0
    seen: set[str] = set()
    for fetched in result.items:
        title = fetched.title.strip()
        if not title:
            continue
        external_id = fetched.external_id[:512]
        if external_id in seen:
            continue
        seen.add(external_id)
        stmt = (
            sqlite_insert(Item)
            .values(
                source_id=source.id,
                external_id=external_id,
                title=title[:512],
                url=(fetched.url or "")[:2000] or None,
                summary=snippet(fetched.summary) or None,
                published_at=fetched.published_at,
                content_hash=content_hash(title, fetched.url),
                is_noise=looks_like_noise(title, fetched.summary),
                fetched_at=now,
            )
            .on_conflict_do_nothing(index_elements=["source_id", "external_id"])
        )
        res = await session.execute(stmt)
        added += res.rowcount or 0
    await session.flush()
    return added


async def apply_fetch(session: AsyncSession, source: Source) -> FetchResult:
    result = await fetch_url(source.kind, source.url)
    await persist_fetch(session, source, result)
    return result
