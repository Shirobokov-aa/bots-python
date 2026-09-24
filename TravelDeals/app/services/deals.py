from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any
import logging

import yaml
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.models import PostedDeal, PriceAlert
from app.services.cities import city_photo
from app.services.travelpayouts import (
    FlightDeal,
    HotelDeal,
    TourDeal,
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
            "flight_max_price_rub": 15000,
            "hotel_max_price_pn_rub": 8000,
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
    airline = f"\nАвиакомпания: {deal.airline}" if deal.airline else ""
    return (
        f"✈️ <b>{deal.title}</b>\n"
        f"Цена от <b>{deal.price:,} ₽</b> · {transfers}{airline}\n\n"
        f'<a href="{deal.link}">Смотреть на Aviasales</a>'
    ).replace(",", " ")


def hotel_caption(deal: HotelDeal) -> str:
    total = ""
    if deal.price_total:
        total = f"\nЗа период: ~{deal.price_total:,} ₽".replace(",", " ")
    return (
        f"🏨 <b>{deal.title}</b>\n"
        f"От <b>{deal.price:,} ₽</b>/ночь{total}\n"
        f"{deal.check_in} → {deal.check_out}\n\n"
        f'<a href="{deal.link}">Смотреть на Hotellook</a>'
    ).replace(",", " ")


def tour_caption(deal: TourDeal) -> str:
    return (
        f"🧳 <b>{deal.title}</b>\n"
        f"Авиа от {deal.flight.price:,} ₽ + отель от {deal.hotel.price:,} ₽/ночь\n"
        f"Ориентир пакета: <b>~{deal.price:,} ₽</b>\n"
        f"Вылет {deal.flight.depart_date}"
        + (f", обратно {deal.flight.return_date}" if deal.flight.return_date else "")
        + f"\nОтель: {deal.hotel.check_in} → {deal.hotel.check_out}\n\n"
        f'<a href="{deal.flight.link}">Билеты</a> · '
        f'<a href="{deal.hotel.link}">Отель</a>'
    ).replace(",", " ")


def deal_photo(deal: FlightDeal | HotelDeal | TourDeal) -> str:
    if isinstance(deal, HotelDeal):
        return deal.photo_url or city_photo(deal.city_iata)
    if isinstance(deal, TourDeal):
        return deal.photo_url or city_photo(deal.flight.destination)
    return city_photo(deal.destination)


def deal_dedupe(deal: FlightDeal | HotelDeal | TourDeal) -> str:
    if isinstance(deal, FlightDeal):
        dates = f"{deal.depart_date}:{deal.return_date or '-'}"
        return dedupe_key("flight", deal.origin, deal.destination, dates, deal.price)
    if isinstance(deal, HotelDeal):
        dates = f"{deal.check_in}:{deal.check_out}"
        return dedupe_key("hotel", "-", deal.city_iata, dates, deal.price)
    dates = f"{deal.flight.depart_date}:{deal.hotel.check_in}"
    return dedupe_key("tour", deal.flight.origin, deal.flight.destination, dates, deal.price)


async def collect_channel_candidates(
    client: TravelpayoutsClient | None = None,
) -> list[FlightDeal | HotelDeal | TourDeal]:
    client = client or get_tp_client()
    cfg = load_routes()
    origins = [o.upper() for o in cfg.get("origins") or ["MOW"]]
    destinations = [d.upper() for d in cfg.get("destinations") or ["AYT"]]
    flight_cap = cfg.get("flight_max_price_rub")
    hotel_cap = cfg.get("hotel_max_price_pn_rub")
    max_posts = int(cfg.get("max_posts_per_tick") or 3)

    flights: list[FlightDeal] = []
    hotels: list[HotelDeal] = []

    for origin in origins:
        for dest in destinations:
            if origin == dest:
                continue
            batch = await client.latest_flights(origin, dest, limit=10)
            for deal in batch:
                if flight_cap and deal.price > int(flight_cap):
                    continue
                flights.append(deal)

    check_in = date.today() + timedelta(days=21)
    check_out = check_in + timedelta(days=7)
    for dest in destinations:
        batch = await client.hotels(dest, check_in, check_out, limit=5)
        for deal in batch:
            if hotel_cap and deal.price > int(hotel_cap):
                continue
            hotels.append(deal)

    flights.sort(key=lambda d: d.price)
    hotels.sort(key=lambda d: d.price)

    tours: list[TourDeal] = []
    # Match flight dest with hotel city
    hotels_by_city: dict[str, HotelDeal] = {}
    for h in hotels:
        hotels_by_city.setdefault(h.city_iata, h)

    for fl in flights:
        hotel = hotels_by_city.get(fl.destination)
        if hotel:
            tours.append(TourDeal(flight=fl, hotel=hotel))
            if len(tours) >= 2:
                break

    # Mix: prefer cheapest flight, hotel, tour
    pool: list[FlightDeal | HotelDeal | TourDeal] = []
    if flights:
        pool.append(flights[0])
    if hotels:
        pool.append(hotels[0])
    if tours:
        pool.append(tours[0])
    # fill remaining with next cheapest flights
    for fl in flights[1:]:
        if len(pool) >= max_posts:
            break
        if fl not in pool:
            pool.append(fl)

    return pool[:max_posts]


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
