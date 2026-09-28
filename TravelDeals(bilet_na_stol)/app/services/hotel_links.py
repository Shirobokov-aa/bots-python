"""Hotel search deeplinks (no price API — Hotellook closed).

Build brand search URLs, optionally wrap via Travelpayouts Links API for CPA + erid.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from urllib.parse import quote, urlencode
import logging

import httpx

from app.config import get_settings
from app.services.cities import CITIES, City, city_name

log = logging.getLogger("traveldeals.hotel_links")

LINKS_API = "https://api.travelpayouts.com/links/v1/create"
DEFAULT_HOTEL_NIGHTS = 7


def hotel_dates_for_flight(
    depart_date: str,
    return_date: str | None = None,
    *,
    default_nights: int = DEFAULT_HOTEL_NIGHTS,
) -> tuple[date, date]:
    """Align hotel stay with flight: check-in = depart, check-out = return or +N nights."""
    check_in = date.fromisoformat(depart_date[:10])
    if return_date:
        check_out = date.fromisoformat(return_date[:10])
        if check_out > check_in:
            return check_in, check_out
    return check_in, check_in + timedelta(days=max(default_nights, 1))


@dataclass(frozen=True)
class HotelDeeplink:
    city_iata: str
    check_in: date
    check_out: date
    ostrovok_url: str
    yandex_url: str
    otello_url: str | None = None

    @property
    def nights(self) -> int:
        return max((self.check_out - self.check_in).days, 1)

    @property
    def title(self) -> str:
        return f"Отели · {city_name(self.city_iata)}"

    @property
    def deal_type(self) -> str:
        return "hotel_link"


def _dates_ddmmyyyy(check_in: date, check_out: date) -> str:
    # Ostrovok keeps these in redirect; ISO "YYYY-MM-DD.YYYY-MM-DD" often drops
    return f"{check_in.strftime('%d.%m.%Y')}-{check_out.strftime('%d.%m.%Y')}"


def ostrovok_search_url(city: City, check_in: date, check_out: date, adults: int = 2) -> str:
    dates = _dates_ddmmyyyy(check_in, check_out)
    if city.ostrovok_path:
        return (
            f"https://ostrovok.ru/hotel/{city.ostrovok_path}/"
            f"?dates={dates}&guests={adults}"
        )
    q = urlencode({"q": city.name_ru, "dates": dates, "guests": adults}, quote_via=quote)
    return f"https://ostrovok.ru/hotel/?{q}"


def yandex_hotels_url(city: City, check_in: date, check_out: date, adults: int = 2) -> str:
    params = urlencode(
        {
            "checkinDate": check_in.isoformat(),
            "checkoutDate": check_out.isoformat(),
            "adults": adults,
        }
    )
    if city.yandex_slug:
        return f"https://travel.yandex.ru/hotels/{city.yandex_slug}/?{params}"
    # fallback: query text (city may not preselect)
    q = urlencode(
        {
            "text": city.name_ru,
            "checkinDate": check_in.isoformat(),
            "checkoutDate": check_out.isoformat(),
            "adults": adults,
        },
        quote_via=quote,
    )
    return f"https://travel.yandex.ru/hotels/?{q}"


def otello_search_url(city: City, check_in: date, check_out: date) -> str | None:
    """Otello = 2GIS/Sber, mostly RU. High CPA; often asks Sber ID login."""
    if not city.otello_slug:
        return None
    q = urlencode(
        {
            "checkin": check_in.isoformat(),
            "checkout": check_out.isoformat(),
        }
    )
    return f"https://otello.ru/hotels/{city.otello_slug}?{q}"


def build_hotel_deeplink(
    city_iata: str,
    check_in: date | None = None,
    check_out: date | None = None,
    *,
    nights: int | None = None,
) -> HotelDeeplink | None:
    city = CITIES.get(city_iata.upper())
    if city is None:
        return None
    if check_in is None:
        check_in = date.today() + timedelta(days=21)
    if check_out is None:
        n = nights if nights and nights > 0 else DEFAULT_HOTEL_NIGHTS
        check_out = check_in + timedelta(days=n)
    return HotelDeeplink(
        city_iata=city.iata,
        check_in=check_in,
        check_out=check_out,
        ostrovok_url=ostrovok_search_url(city, check_in, check_out),
        yandex_url=yandex_hotels_url(city, check_in, check_out),
        otello_url=otello_search_url(city, check_in, check_out),
    )


async def affiliate_wrap(url: str, *, sub_id: str | None = None) -> str:
    """Convert brand URL → Travelpayouts partner link. Fallback: original url."""
    settings = get_settings()
    token = settings.travelpayouts_token.strip()
    marker = settings.travelpayouts_marker.strip()
    trs = settings.trs_id
    if not token or not marker or trs is None:
        return url

    body: dict = {
        "trs": trs,
        "marker": int(marker) if marker.isdigit() else marker,
        "shorten": True,
        "links": [{"url": url, **({"sub_id": sub_id} if sub_id else {})}],
    }
    try:
        async with httpx.AsyncClient(timeout=settings.http_timeout) as client:
            resp = await client.post(
                LINKS_API,
                headers={"X-Access-Token": token, "Content-Type": "application/json"},
                json=body,
            )
            if resp.status_code >= 400:
                log.warning("links api %s: %s", resp.status_code, resp.text[:200])
                return url
            data = resp.json()
    except Exception as exc:
        log.warning("links api fail: %s", exc)
        return url

    partner = _extract_partner_url(data)
    return partner or url


def _extract_partner_url(data: object) -> str | None:
    if not isinstance(data, dict):
        return None
    buckets: list = []
    result = data.get("result")
    if isinstance(result, dict) and isinstance(result.get("links"), list):
        buckets = result["links"]
    elif isinstance(data.get("links"), list):
        buckets = data["links"]
    elif isinstance(result, list):
        buckets = result
    for item in buckets:
        if isinstance(item, dict):
            for key in ("partner_url", "partnerUrl", "url", "short_url"):
                val = item.get(key)
                if isinstance(val, str) and val.startswith("http"):
                    return val
    return None


async def wrap_hotel_deeplink(offer: HotelDeeplink, *, sub_id: str | None = None) -> HotelDeeplink:
    ost = await affiliate_wrap(offer.ostrovok_url, sub_id=sub_id)
    yan = await affiliate_wrap(offer.yandex_url, sub_id=sub_id)
    otel = None
    if offer.otello_url:
        otel = await affiliate_wrap(offer.otello_url, sub_id=sub_id)
    return HotelDeeplink(
        city_iata=offer.city_iata,
        check_in=offer.check_in,
        check_out=offer.check_out,
        ostrovok_url=ost,
        yandex_url=yan,
        otello_url=otel,
    )
