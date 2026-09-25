from __future__ import annotations

import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Destination, QueueItem, Route, SeenPost
from app.services import ai
from app.utils.time import utcnow

log = logging.getLogger("channelmirror.queue")


async def mark_seen(
    session: AsyncSession,
    source_id: int,
    message_id: int,
    grouped_id: int | None,
) -> bool:
    """Return True if newly seen, False if duplicate."""
    result = await session.execute(
        select(SeenPost).where(SeenPost.source_id == source_id, SeenPost.message_id == message_id)
    )
    if result.scalar_one_or_none():
        return False
    session.add(
        SeenPost(
            source_id=source_id,
            message_id=message_id,
            grouped_id=grouped_id,
            seen_at=utcnow(),
        )
    )
    return True


async def enqueue_for_routes(
    session: AsyncSession,
    routes: list[Route],
    source_message_id: int,
    payload: dict[str, Any],
) -> int:
    """Enqueue silent-copy payload for each route. Returns created count.

    # TODO(ai): call transform_payload once and share across routes
    """
    # TODO(ai): should_publish — drop noise before queue
    if not await ai.should_publish(payload):
        log.info("ai skipped message %s", source_message_id)
        return 0

    transformed = await ai.transform_payload(payload)
    body = json.dumps(transformed, ensure_ascii=False)
    created = 0
    for route in routes:
        if not route.is_active:
            continue
        item = QueueItem(
            route_id=route.id,
            source_message_id=source_message_id,
            status="pending",
            payload_json=body,
        )
        session.add(item)
        created += 1
    await session.flush()
    return created


async def next_pending_for_destination(
    session: AsyncSession,
    destination_id: int,
) -> QueueItem | None:
    result = await session.execute(
        select(QueueItem)
        .join(Route, Route.id == QueueItem.route_id)
        .where(
            Route.destination_id == destination_id,
            Route.is_active.is_(True),
            QueueItem.status == "pending",
        )
        .options(
            selectinload(QueueItem.route).selectinload(Route.destination),
            selectinload(QueueItem.route).selectinload(Route.source),
        )
        .order_by(QueueItem.id)
        .limit(1)
    )
    return result.scalar_one_or_none()


async def destinations_due(session: AsyncSession) -> list[Destination]:
    """Destinations that have pending items and interval elapsed."""
    result = await session.execute(
        select(Destination).where(Destination.is_active.is_(True)).order_by(Destination.id)
    )
    dests = list(result.scalars().all())
    due: list[Destination] = []
    now = utcnow()
    for dest in dests:
        pending = await next_pending_for_destination(session, dest.id)
        if pending is None:
            continue
        interval = pending.route.interval_seconds
        if dest.last_posted_at is None:
            due.append(dest)
            continue
        elapsed = (now - dest.last_posted_at).total_seconds()
        if elapsed >= interval:
            due.append(dest)
    return due


async def mark_posted(session: AsyncSession, item: QueueItem, dest: Destination) -> None:
    item.status = "posted"
    item.posted_at = utcnow()
    dest.last_posted_at = item.posted_at


async def mark_failed(session: AsyncSession, item: QueueItem, error: str) -> None:
    item.status = "failed"
    item.error = error[:2000]
