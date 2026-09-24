from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import Source, User
from app.ingest.parse_source import ParsedSource


class SourceLimitError(Exception):
    pass


class DuplicateSourceError(Exception):
    pass


def interval_for(user: User) -> int:
    settings = get_settings()
    return settings.vip_interval_seconds if user.is_vip else settings.free_interval_seconds


def max_sources(user: User) -> int:
    settings = get_settings()
    return settings.vip_max_sources if user.is_vip else settings.free_max_sources


def digest_limit(user: User) -> int:
    settings = get_settings()
    return settings.vip_digest_items if user.is_vip else settings.free_digest_items


async def list_sources(session: AsyncSession, user_id: int) -> list[Source]:
    result = await session.execute(
        select(Source).where(Source.user_id == user_id).order_by(Source.id.asc())
    )
    return list(result.scalars())


async def count_active(session: AsyncSession, user_id: int) -> int:
    result = await session.execute(
        select(func.count()).select_from(Source).where(Source.user_id == user_id, Source.is_active.is_(True))
    )
    return int(result.scalar_one())


async def get_user_source(session: AsyncSession, user_id: int, source_id: int) -> Source | None:
    result = await session.execute(
        select(Source).where(Source.id == source_id, Source.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def add_source(
    session: AsyncSession,
    user: User,
    parsed: ParsedSource,
    *,
    title: str | None = None,
    fetch_url: str | None = None,
    kind: str | None = None,
) -> Source:
    url = fetch_url or parsed.url
    existing = await session.execute(select(Source).where(Source.user_id == user.id, Source.url == url))
    if existing.scalar_one_or_none() is not None:
        raise DuplicateSourceError("Этот источник уже добавлен.")
    if await count_active(session, user.id) >= max_sources(user):
        raise SourceLimitError(f"Лимит источников: {max_sources(user)}. Удали лишнее или бери /vip")
    source = Source(
        user_id=user.id,
        kind=kind or parsed.kind,
        url=url,
        display_url=parsed.display,
        title=title or parsed.display,
        interval_seconds=interval_for(user),
    )
    session.add(source)
    await session.flush()
    return source


async def delete_source(session: AsyncSession, source: Source) -> None:
    await session.delete(source)
    await session.flush()


async def toggle_source(session: AsyncSession, source: Source) -> Source:
    source.is_active = not source.is_active
    if source.is_active:
        source.consecutive_errors = 0
        source.last_error = None
    await session.flush()
    return source
