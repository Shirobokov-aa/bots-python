from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
import logging
from typing import Any

import httpx

from app.config import get_settings
from app.services.cities import CITIES, city_name

log = logging.getLogger("traveldeals.tp")

API = "https://api.travelpayouts.com"
ENGINE = "https://engine.hotellook.com"


@dataclass
class FlightDeal:
    origin: str
    destination: str
    price: int
    depart_date: str  # YYYY-MM-DD
    return_date: str | None
    airline: str | None
    transfers: int
    link: str
    deal_type: str = "flight"

    @property
    def title(self) -> str:
        ret = f" → {self.return_date}" if self.return_date else " (в одну сторону)"
        return f"{city_name(self.origin)} → {city_name(self.destination)}, {self.depart_date}{ret}"


@dataclass
class HotelDeal:
    city_iata: str
    hotel_name: str
    price: int  # total or per night — we store price_pn when possible
    price_total: int | None
    check_in: str
    check_out: str
    stars: int | None
    hotel_id: int | None
    photo_url: str | None
    link: str
    deal_type: str = "hotel"

    @property
    def title(self) -> str:
        stars = f", {self.stars}★" if self.stars else ""
        return f"{self.hotel_name}{stars} · {city_name(self.city_iata)}"


@dataclass
class TourDeal:
    flight: FlightDeal
    hotel: HotelDeal
    deal_type: str = "tour"

    @property
    def price(self) -> int:
        hotel_part = self.hotel.price_total or self.hotel.price
        return self.flight.price + hotel_part

    @property
    def title(self) -> str:
        return (
            f"Тур: {city_name(self.flight.origin)} → {city_name(self.flight.destination)} "
            f"+ {self.hotel.hotel_name}"
        )

    @property
    def link(self) -> str:
        return self.flight.link

    @property
    def photo_url(self) -> str | None:
        return self.hotel.photo_url


def _ddmm(d: date) -> str:
    return d.strftime("%d%m")


def flight_search_link(
    origin: str,
    destination: str,
    depart: date,
    return_d: date | None,
    marker: str,
) -> str:
    """Aviasales search deeplink with affiliate marker."""
    origin = origin.upper()
    destination = destination.upper()
    if return_d:
        path = f"{origin}{_ddmm(depart)}{destination}{_ddmm(return_d)}1"
    else:
        path = f"{origin}{_ddmm(depart)}{destination}1"
    base = f"https://www.aviasales.ru/search/{path}"
    if marker:
        return f"{base}?marker={marker}"
    return base


def hotel_search_link(
    city_name_ru: str,
    check_in: date,
    check_out: date,
    marker: str,
    hotel_id: int | None = None,
) -> str:
    params = (
        f"checkIn={check_in.isoformat()}&checkOut={check_out.isoformat()}"
        f"&adults=2&currency=rub&language=ru"
    )
    if hotel_id:
        url = f"https://search.hotellook.com/hotels?hotelId={hotel_id}&{params}"
    else:
        from urllib.parse import quote

        url = f"https://search.hotellook.com/?destination={quote(city_name_ru)}&{params}"
    if marker:
        return f"{url}&marker={marker}"
    return url


def price_bucket(price: int) -> int:
    """Round price for dedupe (500 RUB steps)."""
    return (price // 500) * 500


def dedupe_key(
    deal_type: str,
    origin: str,
    dest: str,
    dates: str,
    price: int,
) -> str:
    return f"{deal_type}:{origin}:{dest}:{dates}:{price_bucket(price)}"


class TravelpayoutsClient:
    def __init__(self, token: str | None = None, marker: str | None = None, timeout: float | None = None):
        settings = get_settings()
        self.token = token if token is not None else settings.travelpayouts_token
        self.marker = marker if marker is not None else settings.travelpayouts_marker
        self.timeout = timeout if timeout is not None else settings.http_timeout
        self._client: httpx.AsyncClient | None = None

    async def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            headers = {}
            if self.token:
                headers["X-Access-Token"] = self.token
            self._client = httpx.AsyncClient(timeout=self.timeout, headers=headers)
        return self._client

    async def aclose(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def latest_flights(
        self,
        origin: str,
        destination: str | None = None,
        *,
        limit: int = 30,
        one_way: bool = False,
    ) -> list[FlightDeal]:
        params: dict[str, Any] = {
            "origin": origin.upper(),
            "currency": "rub",
            "period_type": "month",
            "page": 1,
            "limit": limit,
            "show_to_affiliates": "true",
            "sorting": "price",
            "trip_class": 0,
            "one_way": "true" if one_way else "false",
        }
        if destination:
            params["destination"] = destination.upper()
        if self.token:
            params["token"] = self.token

        client = await self._http()
        url = f"{API}/v2/prices/latest"
        try:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            log.warning("latest_flights fail %s→%s: %s", origin, destination, exc)
            return []

        deals: list[FlightDeal] = []
        for row in data.get("data") or []:
            try:
                depart = row["depart_date"]
                ret = row.get("return_date")
                price = int(row["value"])
                dest = row.get("destination") or destination or ""
                org = row.get("origin") or origin
                depart_d = date.fromisoformat(depart[:10])
                return_d = date.fromisoformat(ret[:10]) if ret else None
                deals.append(
                    FlightDeal(
                        origin=org.upper(),
                        destination=dest.upper(),
                        price=price,
                        depart_date=depart_d.isoformat(),
                        return_date=return_d.isoformat() if return_d else None,
                        airline=row.get("airline"),
                        transfers=int(row.get("number_of_changes") or 0),
                        link=flight_search_link(org, dest, depart_d, return_d, self.marker),
                    )
                )
            except (KeyError, TypeError, ValueError) as exc:
                log.debug("skip flight row: %s", exc)
        deals.sort(key=lambda d: d.price)
        return deals

    async def calendar_flights(
        self,
        origin: str,
        destination: str,
        month: str | None = None,
    ) -> list[FlightDeal]:
        """month: YYYY-MM"""
        if not month:
            month = date.today().strftime("%Y-%m")
        params: dict[str, Any] = {
            "origin": origin.upper(),
            "destination": destination.upper(),
            "depart_date": month,
            "calendar_type": "departure_date",
            "currency": "rub",
        }
        if self.token:
            params["token"] = self.token

        client = await self._http()
        try:
            resp = await client.get(f"{API}/v1/prices/calendar", params=params)
            resp.raise_for_status()
            data = resp.json()
        except Exception as exc:
            log.warning("calendar fail %s→%s: %s", origin, destination, exc)
            return []

        deals: list[FlightDeal] = []
        raw = data.get("data") or {}
        if isinstance(raw, dict):
            rows = raw.values()
        else:
            rows = raw
        for row in rows:
            try:
                depart = row["departure_at"][:10] if "departure_at" in row else row.get("depart_date")
                if not depart:
                    continue
                price = int(row.get("price") or row.get("value"))
                depart_d = date.fromisoformat(str(depart)[:10])
                deals.append(
                    FlightDeal(
                        origin=origin.upper(),
                        destination=destination.upper(),
                        price=price,
                        depart_date=depart_d.isoformat(),
                        return_date=None,
                        airline=row.get("airline"),
                        transfers=int(row.get("transfers") or row.get("number_of_changes") or 0),
                        link=flight_search_link(origin, destination, depart_d, None, self.marker),
                    )
                )
            except (KeyError, TypeError, ValueError):
                continue
        deals.sort(key=lambda d: d.price)
        return deals

    async def hotels(
        self,
        city_iata: str,
        check_in: date | None = None,
        check_out: date | None = None,
        *,
        limit: int = 5,
    ) -> list[HotelDeal]:
        city = CITIES.get(city_iata.upper())
        if city is None or city.hotellook_id is None:
            log.warning("no hotellook id for %s", city_iata)
            return []

        if check_in is None:
            check_in = date.today() + timedelta(days=14)
        if check_out is None:
            check_out = check_in + timedelta(days=7)

        params: dict[str, Any] = {
            "id": city.hotellook_id,
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "currency": "rub",
            "language": "ru",
            "limit": limit,
            "type": "popularity",
        }
        if self.token:
            params["token"] = self.token

        client = await self._http()
        deals: list[HotelDeal] = []

        # Primary: Travelpayouts hotellook selections
        try:
            resp = await client.get(f"{API}/hotellook/v1/hotels", params=params)
            if resp.status_code == 200:
                payload = resp.json()
                deals.extend(self._parse_hotellook_payload(city_iata, check_in, check_out, payload))
        except Exception as exc:
            log.warning("hotellook/v1 fail %s: %s", city_iata, exc)

        if deals:
            return deals

        # Fallback: engine cache
        try:
            cache_params = {
                "locationId": city.hotellook_id,
                "checkIn": check_in.isoformat(),
                "checkOut": check_out.isoformat(),
                "currency": "rub",
                "limit": limit,
            }
            if self.token:
                cache_params["token"] = self.token
            resp = await client.get(f"{ENGINE}/api/v2/cache.json", params=cache_params)
            resp.raise_for_status()
            payload = resp.json()
            deals.extend(self._parse_cache_payload(city_iata, check_in, check_out, payload))
        except Exception as exc:
            log.warning("hotellook cache fail %s: %s", city_iata, exc)

        deals.sort(key=lambda d: d.price)
        return deals

    def _parse_hotellook_payload(
        self,
        city_iata: str,
        check_in: date,
        check_out: date,
        payload: Any,
    ) -> list[HotelDeal]:
        rows: list[Any] = []
        if isinstance(payload, dict):
            for value in payload.values():
                if isinstance(value, list):
                    rows.extend(value)
                elif isinstance(value, dict) and "hotel_id" in value:
                    rows.append(value)
        elif isinstance(payload, list):
            rows = payload

        out: list[HotelDeal] = []
        for row in rows:
            deal = self._hotel_from_row(city_iata, check_in, check_out, row)
            if deal:
                out.append(deal)
        return out

    def _parse_cache_payload(
        self,
        city_iata: str,
        check_in: date,
        check_out: date,
        payload: Any,
    ) -> list[HotelDeal]:
        rows = payload if isinstance(payload, list) else payload.get("hotels") or []
        out: list[HotelDeal] = []
        for row in rows:
            deal = self._hotel_from_row(city_iata, check_in, check_out, row)
            if deal:
                out.append(deal)
        return out

    def _hotel_from_row(
        self,
        city_iata: str,
        check_in: date,
        check_out: date,
        row: dict[str, Any],
    ) -> HotelDeal | None:
        try:
            name = row.get("hotelName") or row.get("name") or "Отель"
            hotel_id = row.get("hotelId") or row.get("hotel_id")
            stars = row.get("stars")
            if stars is not None:
                stars = int(stars)

            price_info = row.get("last_price_info") or {}
            price_pn = price_info.get("price_pn") or row.get("priceFrom") or row.get("price")
            price_total = price_info.get("price")
            if price_pn is None and price_total is None:
                return None
            price_pn_i = int(price_pn or 0)
            price_total_i = int(price_total) if price_total is not None else None
            if price_pn_i <= 0 and price_total_i:
                nights = max((check_out - check_in).days, 1)
                price_pn_i = price_total_i // nights

            photo = None
            if row.get("photoUrl"):
                photo = row["photoUrl"]
            elif row.get("photos") and isinstance(row["photos"], list) and row["photos"]:
                photo = str(row["photos"][0])

            city = CITIES.get(city_iata.upper())
            link = hotel_search_link(
                city.name_ru if city else city_iata,
                check_in,
                check_out,
                self.marker,
                int(hotel_id) if hotel_id else None,
            )
            return HotelDeal(
                city_iata=city_iata.upper(),
                hotel_name=str(name)[:200],
                price=price_pn_i,
                price_total=price_total_i,
                check_in=check_in.isoformat(),
                check_out=check_out.isoformat(),
                stars=stars,
                hotel_id=int(hotel_id) if hotel_id else None,
                photo_url=photo,
                link=link,
            )
        except (TypeError, ValueError, KeyError):
            return None


_client: TravelpayoutsClient | None = None


def get_tp_client() -> TravelpayoutsClient:
    global _client
    if _client is None:
        _client = TravelpayoutsClient()
    return _client


async def close_tp_client() -> None:
    global _client
    if _client:
        await _client.aclose()
        _client = None
