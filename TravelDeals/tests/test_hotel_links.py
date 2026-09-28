from datetime import date

from app.services.cities import resolve_city
from app.services.hotel_links import (
    build_hotel_deeplink,
    hotel_dates_for_flight,
    ostrovok_search_url,
)
from app.services.deals import flight_caption
from app.services.travelpayouts import FlightDeal


def test_typo_analya():
    assert resolve_city("аналья").iata == "AYT"


def test_ostrovok_city_path_keeps_dates():
    city = resolve_city("Москва")
    assert city is not None
    url = ostrovok_search_url(city, date(2026, 10, 19), date(2026, 10, 29))
    assert "/hotel/russia/moscow/" in url
    assert "19.10.2026-29.10.2026" in url
    assert "hotel/search" not in url


def test_build_hotel_deeplink_moscow():
    offer = build_hotel_deeplink("MOW", nights=10)
    assert offer is not None
    assert "/hotels/moscow/" in offer.yandex_url
    assert "checkinDate=" in offer.yandex_url
    assert offer.otello_url and "otello.ru/hotels/moscow" in offer.otello_url


def test_build_hotel_deeplink_ayt_no_otello():
    offer = build_hotel_deeplink("AYT", nights=7)
    assert offer is not None
    assert "/hotel/turkey/antalya/" in offer.ostrovok_url
    assert offer.otello_url is None


def test_hotel_dates_roundtrip():
    check_in, check_out = hotel_dates_for_flight("2026-10-01", "2026-10-10")
    assert check_in == date(2026, 10, 1)
    assert check_out == date(2026, 10, 10)


def test_hotel_dates_one_way_default_nights():
    check_in, check_out = hotel_dates_for_flight("2026-10-01", None, default_nights=7)
    assert check_in == date(2026, 10, 1)
    assert check_out == date(2026, 10, 8)


def test_hotel_deeplink_from_flight_dates():
    check_in, check_out = hotel_dates_for_flight("2026-11-05", "2026-11-12")
    offer = build_hotel_deeplink("IST", check_in=check_in, check_out=check_out)
    assert offer is not None
    assert offer.check_in == date(2026, 11, 5)
    assert offer.check_out == date(2026, 11, 12)
    assert "05.11.2026-12.11.2026" in offer.ostrovok_url


def test_flight_caption_calm():
    deal = FlightDeal(
        origin="MOW",
        destination="AYT",
        price=9900,
        depart_date="2026-06-15",
        return_date="2026-06-22",
        airline="SU",
        transfers=0,
        link="https://example.com",
    )
    text = flight_caption(deal)
    assert "✈️" not in text
    assert "Hotellook" not in text
    assert "от" in text and "9 900" in text
    assert "Смотреть билеты" in text
