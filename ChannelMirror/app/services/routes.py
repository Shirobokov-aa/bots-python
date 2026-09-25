from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import get_settings
from app.db.models import Destination, Route, Source


class DuplicateError(Exception):
    pass


async def list_destinations(session: AsyncSession, user_id: int) -> list[Destination]:
    result = await session.execute(
        select(Destination).where(Destination.user_id == user_id).order_by(Destination.id)
    )
    return list(result.scalars().all())


async def list_sources(session: AsyncSession, user_id: int) -> list[Source]:
    result = await session.execute(select(Source).where(Source.user_id == user_id).order_by(Source.id))
    return list(result.scalars().all())


async def list_routes(session: AsyncSession, user_id: int) -> list[Route]:
    result = await session.execute(
        select(Route)
        .where(Route.user_id == user_id)
        .options(selectinload(Route.source), selectinload(Route.destination))
        .order_by(Route.id)
    )
    return list(result.scalars().all())


async def get_destination(session: AsyncSession, user_id: int, dest_id: int) -> Destination | None:
    result = await session.execute(
        select(Destination).where(Destination.id == dest_id, Destination.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def add_destination(
    session: AsyncSession,
    user_id: int,
    chat_id: int,
    title: str | None,
    username: str | None,
) -> Destination:
    result = await session.execute(
        select(Destination).where(Destination.user_id == user_id, Destination.chat_id == chat_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        existing.title = title or existing.title
        existing.username = username or existing.username
        existing.is_active = True
        return existing
    dest = Destination(
        user_id=user_id,
        chat_id=chat_id,
        title=title,
        username=username.lower() if username else None,
    )
    session.add(dest)
    await session.flush()
    return dest


async def add_source(
    session: AsyncSession,
    user_id: int,
    username: str,
    title: str | None = None,
    chat_id: int | None = None,
) -> Source:
    uname = username.lower().lstrip("@")
    result = await session.execute(select(Source).where(Source.user_id == user_id, Source.username == uname))
    existing = result.scalar_one_or_none()
    if existing:
        existing.is_active = True
        if title:
            existing.title = title
        if chat_id is not None:
            existing.chat_id = chat_id
        return existing
    source = Source(user_id=user_id, username=uname, title=title, chat_id=chat_id)
    session.add(source)
    await session.flush()
    return source


async def add_source_by_chat_id(
    session: AsyncSession,
    user_id: int,
    chat_id: int,
    title: str | None = None,
    username: str | None = None,
) -> Source:
    """Private/public source keyed by Telegram peer id."""
    result = await session.execute(
        select(Source).where(Source.user_id == user_id, Source.chat_id == chat_id)
    )
    existing = result.scalar_one_or_none()
    slug = (username or f"id{abs(int(chat_id))}").lower().lstrip("@")
    if existing:
        existing.is_active = True
        if title:
            existing.title = title
        if username:
            existing.username = slug
        return existing
    # also merge if same slug already exists without chat_id
    by_name = await session.execute(select(Source).where(Source.user_id == user_id, Source.username == slug))
    named = by_name.scalar_one_or_none()
    if named:
        named.is_active = True
        named.chat_id = chat_id
        if title:
            named.title = title
        return named
    source = Source(user_id=user_id, username=slug, title=title, chat_id=chat_id)
    session.add(source)
    await session.flush()
    return source


async def add_route(
    session: AsyncSession,
    user_id: int,
    source_id: int,
    destination_id: int,
    interval_seconds: int | None = None,
    show_source_label: bool | None = None,
) -> Route:
    result = await session.execute(
        select(Route).where(Route.source_id == source_id, Route.destination_id == destination_id)
    )
    existing = result.scalar_one_or_none()
    if existing:
        if existing.user_id != user_id:
            raise DuplicateError("маршрут чужой")
        existing.is_active = True
        if interval_seconds is not None:
            existing.interval_seconds = interval_seconds
        if show_source_label is not None:
            existing.show_source_label = show_source_label
        return existing
    route = Route(
        user_id=user_id,
        source_id=source_id,
        destination_id=destination_id,
        interval_seconds=interval_seconds or get_settings().post_interval_seconds,
        show_source_label=bool(show_source_label) if show_source_label is not None else False,
    )
    session.add(route)
    await session.flush()
    return route


async def delete_route(session: AsyncSession, user_id: int, route_id: int) -> bool:
    result = await session.execute(select(Route).where(Route.id == route_id, Route.user_id == user_id))
    route = result.scalar_one_or_none()
    if route is None:
        return False
    await session.delete(route)
    return True


async def toggle_route(session: AsyncSession, user_id: int, route_id: int) -> Route | None:
    result = await session.execute(select(Route).where(Route.id == route_id, Route.user_id == user_id))
    route = result.scalar_one_or_none()
    if route is None:
        return None
    route.is_active = not route.is_active
    return route


async def toggle_source_label(session: AsyncSession, user_id: int, route_id: int) -> Route | None:
    result = await session.execute(
        select(Route)
        .where(Route.id == route_id, Route.user_id == user_id)
        .options(selectinload(Route.source), selectinload(Route.destination))
    )
    route = result.scalar_one_or_none()
    if route is None:
        return None
    route.show_source_label = not route.show_source_label
    return route


async def active_sources(session: AsyncSession) -> list[Source]:
    result = await session.execute(
        select(Source)
        .join(Route, Route.source_id == Source.id)
        .where(Source.is_active.is_(True), Route.is_active.is_(True))
        .distinct()
    )
    return list(result.scalars().all())


async def active_source_usernames(session: AsyncSession) -> set[str]:
    return {s.username for s in await active_sources(session) if s.username}


async def routes_for_username(session: AsyncSession, username: str) -> list[Route]:
    uname = username.lower().lstrip("@")
    result = await session.execute(
        select(Route)
        .join(Source, Source.id == Route.source_id)
        .where(
            Source.username == uname,
            Source.is_active.is_(True),
            Route.is_active.is_(True),
        )
        .options(selectinload(Route.source), selectinload(Route.destination))
    )
    return list(result.scalars().all())


async def routes_for_chat_id(session: AsyncSession, chat_id: int) -> list[Route]:
    result = await session.execute(
        select(Route)
        .join(Source, Source.id == Route.source_id)
        .where(
            Source.chat_id == chat_id,
            Source.is_active.is_(True),
            Route.is_active.is_(True),
        )
        .options(selectinload(Route.source), selectinload(Route.destination))
    )
    return list(result.scalars().all())
