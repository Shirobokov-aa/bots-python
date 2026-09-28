from __future__ import annotations

from pathlib import Path
from typing import Any
import logging

import yaml
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import PostedDeal, PriceAlert
from app.services.cities import city_name, city_photo
from app.services.travelpayouts import (
    FlightDeal,
    TravelpayoutsClient,
    dedupe_key,
    get_tp_client,
)
from app.utils.time import utcnow

log = logging.getLogger("traveldeals.deals")


def load_routes() -> dict[str, Any]:
    path = Path(get_settings().routes_file)
    if not path.exists():
        return {
            "origins": ["MOW", "LED"],
            "destinations": ["AYT", "IST", "DXB", "BKK", "AER"],
            "flight_max_price_rub": 18000,
            "max_posts_per_tick": 3,
        }
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


async def is_posted(session: AsyncSession, key: str) -> bool:
    result = await session.execute(select(PostedDeal).where(PostedDeal.dedupe_key == key))
    return result.scalar_one_or_none() is not None


async def mark_posted(
    session: AsyncSession,
    *,
    key: str,
    deal_type: str,
    title: str,
    price: int,
    link: str,
    to_channel: bool,
) -> None:
    session.add(
        PostedDeal(
            dedupe_key=key,
            deal_type=deal_type,
            title=title[:500],
            price=price,
            link=link,
            posted_to_channel=to_channel,
        )
    )


def flight_caption(deal: FlightDeal) -> str:
    transfers = "прямой" if deal.transfers == 0 else f"пересадок: {deal.transfers}"
    airline = f" · {deal.airline}" if deal.airline else ""
    ret = f"\nОбратно: {deal.return_date}" if deal.return_date else ""
    return (
        f"<b>{city_name(deal.origin)} → {city_name(deal.destination)}</b>\n"
        f"от <b>{deal.price:,} ₽</b> · {transfers}{airline}\n"
        f"Вылет {deal.depart_date}{ret}\n\n"
        f'<a href="{deal.link}">Смотреть билеты</a>'
    ).replace(",", " ")


def deal_photo(deal: FlightDeal) -> str:
    return city_photo(deal.destination)


def deal_dedupe(deal: FlightDeal) -> str:
    dates = f"{deal.depart_date}:{deal.return_date or '-'}"
    return dedupe_key("flight", deal.origin, deal.destination, dates, deal.price)


async def collect_channel_candidates(
    client: TravelpayoutsClient | None = None,
) -> list[FlightDeal]:
    """Flights only — hotels are deeplinks on the post (no price API)."""
    client = client or get_tp_client()
    cfg = load_routes()
    origins = [o.upper() for o in cfg.get("origins") or ["MOW"]]
    destinations = [d.upper() for d in cfg.get("destinations") or ["AYT"]]
    flight_cap = cfg.get("flight_max_price_rub")
    max_posts = int(cfg.get("max_posts_per_tick") or 3)

    flights: list[FlightDeal] = []
    for origin in origins:
        for dest in destinations:
            if origin == dest:
                continue
            batch = await client.latest_flights(origin, dest, limit=10)
            for deal in batch:
                if flight_cap and deal.price > int(flight_cap):
                    continue
                flights.append(deal)

    flights.sort(key=lambda d: d.price)
    pool: list[FlightDeal] = []
    seen: set[str] = set()
    for fl in flights:
        key = f"{fl.origin}:{fl.destination}:{fl.depart_date}"
        if key in seen:
            continue
        seen.add(key)
        pool.append(fl)
        if len(pool) >= max_posts:
            break
    return pool


async def find_alert_matches(
    session: AsyncSession,
    client: TravelpayoutsClient | None = None,
) -> list[tuple[PriceAlert, FlightDeal]]:
    client = client or get_tp_client()
    result = await session.execute(
        select(PriceAlert)
        .where(PriceAlert.is_active.is_(True))
        .options(selectinload(PriceAlert.user))
    )
    alerts = list(result.scalars().all())
    matches: list[tuple[PriceAlert, FlightDeal]] = []
    for alert in alerts:
        deals = await client.latest_flights(alert.origin, alert.destination, limit=5)
        for deal in deals:
            if deal.price > alert.max_price:
                continue
            if alert.last_notified_price is not None and deal.price >= alert.last_notified_price:
                continue
            matches.append((alert, deal))
            break
    return matches


async def mark_alert_notified(session: AsyncSession, alert: PriceAlert, price: int) -> None:
    alert.last_notified_price = price
    alert.last_notified_at = utcnow()
