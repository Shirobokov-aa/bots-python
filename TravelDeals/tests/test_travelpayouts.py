from datetime import date

from app.services.cities import resolve_city
from app.services.travelpayouts import (
    FlightDeal,
    dedupe_key,
    flight_search_link,
    hotel_search_link,
    price_bucket,
)


def test_resolve_city_ru_and_iata():
    assert resolve_city("Москва").iata == "MOW"
    assert resolve_city("ayt").iata == "AYT"
    assert resolve_city("xyz") is None


def test_flight_search_link_one_way():
    link = flight_search_link("MOW", "AYT", date(2026, 6, 15), None, "marker123")
    assert "MOW1506AYT1" in link
    assert "marker=marker123" in link


def test_flight_search_link_roundtrip():
    link = flight_search_link("LED", "IST", date(2026, 7, 1), date(2026, 7, 10), "m")
    assert "LED0107IST10071" in link
    assert "marker=m" in link


def test_hotel_search_link():
    link = hotel_search_link("Анталья", date(2026, 6, 1), date(2026, 6, 8), "mk", hotel_id=42)
    assert "hotelId=42" in link
    assert "marker=mk" in link
    assert "checkIn=2026-06-01" in link


def test_price_bucket_and_dedupe():
    assert price_bucket(12340) == 12000
    assert price_bucket(12499) == 12000
    key = dedupe_key("flight", "MOW", "AYT", "2026-06-01:-", 12340)
    assert key == "flight:MOW:AYT:2026-06-01:-:12000"


def test_flight_deal_title():
    deal = FlightDeal(
        origin="MOW",
        destination="AYT",
        price=9000,
        depart_date="2026-06-15",
        return_date=None,
        airline="S7",
        transfers=0,
        link="https://example.com",
    )
    assert "Москва" in deal.title
    assert "Анталья" in deal.title
