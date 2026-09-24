from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class FetchedItem:
    external_id: str
    title: str
    url: str | None
    summary: str | None = None
    published_at: datetime | None = None


@dataclass
class FetchResult:
    title: str | None = None
    items: list[FetchedItem] = field(default_factory=list)
    error: str | None = None
    canonical_url: str | None = None
    kind: str | None = None
