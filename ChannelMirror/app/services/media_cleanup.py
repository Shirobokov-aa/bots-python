"""Delete downloaded media after publish; prune old queue rows + orphans."""

from __future__ import annotations

import json
import logging
from datetime import timedelta
from pathlib import Path
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import QueueItem, SeenPost
from app.utils.time import utcnow

log = logging.getLogger("channelmirror.media")


def media_paths_from_payload(payload: dict[str, Any]) -> list[str]:
    paths: list[str] = []
    if payload.get("path"):
        paths.append(str(payload["path"]))
    for item in payload.get("items") or []:
        if isinstance(item, dict) and item.get("path"):
            paths.append(str(item["path"]))
    return paths


def delete_media_files(paths: list[str]) -> int:
    """Unlink files under media_dir only. Returns deleted count."""
    root = Path(get_settings().media_dir).resolve()
    deleted = 0
    for raw in paths:
        try:
            path = Path(raw).resolve()
        except OSError:
            continue
        if root not in path.parents and path != root:
            log.warning("skip delete outside media_dir: %s", raw)
            continue
        if not path.is_file():
            continue
        try:
            path.unlink()
            deleted += 1
        except OSError as exc:
            log.warning("unlink %s failed: %s", path, exc)
    return deleted


def cleanup_payload_media(payload: dict[str, Any]) -> int:
    return delete_media_files(media_paths_from_payload(payload))


async def prune_done_queue(session: AsyncSession, keep_days: int = 7) -> tuple[int, int]:
    """Drop posted/failed rows older than keep_days; delete their media first."""
    cutoff = utcnow() - timedelta(days=keep_days)
    result = await session.execute(
        select(QueueItem).where(
            QueueItem.status.in_(("posted", "failed")),
            QueueItem.created_at < cutoff,
        )
    )
    items = list(result.scalars().all())
    files = 0
    for item in items:
        try:
            payload = json.loads(item.payload_json)
        except json.JSONDecodeError:
            payload = {}
        files += cleanup_payload_media(payload)
        await session.delete(item)
    return len(items), files


async def prune_old_seen(session: AsyncSession, keep_days: int = 30) -> int:
    cutoff = utcnow() - timedelta(days=keep_days)
    result = await session.execute(delete(SeenPost).where(SeenPost.seen_at < cutoff))
    return int(result.rowcount or 0)


def prune_orphan_media(session_payloads: list[str] | None = None) -> int:
    """Delete media files not referenced by given payload JSON strings (pending)."""
    refs: set[str] = set()
    for raw in session_payloads or []:
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            continue
        for p in media_paths_from_payload(payload):
            try:
                refs.add(str(Path(p).resolve()))
            except OSError:
                refs.add(p)

    root = Path(get_settings().media_dir)
    if not root.is_dir():
        return 0
    deleted = 0
    for path in root.iterdir():
        if not path.is_file():
            continue
        try:
            key = str(path.resolve())
        except OSError:
            continue
        if key in refs:
            continue
        try:
            path.unlink()
            deleted += 1
        except OSError as exc:
            log.warning("orphan unlink %s failed: %s", path, exc)
    return deleted


async def collect_pending_payloads(session: AsyncSession) -> list[str]:
    result = await session.execute(
        select(QueueItem.payload_json).where(QueueItem.status == "pending")
    )
    return [row[0] for row in result.all()]


async def run_maintenance(session: AsyncSession) -> None:
    """Prune old rows and orphan media. Safe to call periodically."""
    rows, files = await prune_done_queue(session, keep_days=7)
    seen = await prune_old_seen(session, keep_days=30)
    pending = await collect_pending_payloads(session)
    orphans = prune_orphan_media(pending)
    if rows or files or seen or orphans:
        log.info(
            "maintenance queue_rows=%s media_from_queue=%s seen=%s orphans=%s",
            rows,
            files,
            seen,
            orphans,
        )
