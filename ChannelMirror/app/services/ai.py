"""AI hooks — stubs for later.

MVP: no AI. Every call is a no-op pass-through with TODO markers.
"""

from __future__ import annotations

from typing import Any


async def should_publish(payload: dict[str, Any]) -> bool:
    """Return False to drop a post before queue.

    # TODO(ai): filter ads / spam / off-topic by text+caption
    # TODO(ai): optional vision check on images
    """
    _ = payload
    return True


async def transform_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Rewrite / enrich payload before publish.

    # TODO(ai): rewrite text / caption
    # TODO(ai): strip or replace source mentions inside body
    # TODO(ai): generate own cover image
    """
    return payload
