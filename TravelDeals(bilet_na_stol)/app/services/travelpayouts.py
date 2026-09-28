from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import logging
from typing import Any

import httpx

from app.config import get_settings
from app.services.cities import city_name

log = logging.getLogger("traveldeals.tp")

API = "https://api.travelpayouts.com"


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
