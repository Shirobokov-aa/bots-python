from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class City:
    iata: str
    name_ru: str
    hotellook_id: int | None = None
    photo_url: str = ""


# photo_url: стабильные picsum seeds по городу (fallback для канала)
CITIES: dict[str, City] = {
    "MOW": City("MOW", "Москва", 12153, "https://picsum.photos/seed/mow-travel/800/500"),
    "LED": City("LED", "Санкт-Петербург", 12209, "https://picsum.photos/seed/led-travel/800/500"),
    "SVX": City("SVX", "Екатеринбург", 12230, "https://picsum.photos/seed/svx-travel/800/500"),
    "KZN": City("KZN", "Казань", 12173, "https://picsum.photos/seed/kzn-travel/800/500"),
    "AER": City("AER", "Сочи", 12286, "https://picsum.photos/seed/aer-travel/800/500"),
    "AYT": City("AYT", "Анталья", 2062, "https://picsum.photos/seed/ayt-travel/800/500"),
    "IST": City("IST", "Стамбул", 2341, "https://picsum.photos/seed/ist-travel/800/500"),
    "DXB": City("DXB", "Дубай", 14690, "https://picsum.photos/seed/dxb-travel/800/500"),
    "BKK": City("BKK", "Бангкок", 12822, "https://picsum.photos/seed/bkk-travel/800/500"),
    "HKT": City("HKT", "Пхукет", 12864, "https://picsum.photos/seed/hkt-travel/800/500"),
    "EVN": City("EVN", "Ереван", 12147, "https://picsum.photos/seed/evn-travel/800/500"),
    "BUS": City("BUS", "Батуми", 12219, "https://picsum.photos/seed/bus-travel/800/500"),
}

# RU aliases → IATA
ALIASES: dict[str, str] = {
    "москва": "MOW",
    "мск": "MOW",
    "питер": "LED",
    "спб": "LED",
    "санкт-петербург": "LED",
    "петербург": "LED",
    "екб": "SVX",
    "екатеринбург": "SVX",
    "казань": "KZN",
    "сочи": "AER",
    "адлер": "AER",
    "анталья": "AYT",
    "стамбул": "IST",
    "дубай": "DXB",
    "бангкок": "BKK",
    "пхукет": "HKT",
    "ереван": "EVN",
    "батуми": "BUS",
}


def resolve_city(text: str) -> City | None:
    raw = text.strip()
    if not raw:
        return None
    upper = raw.upper()
    if upper in CITIES:
        return CITIES[upper]
    key = raw.lower().replace("ё", "е")
    iata = ALIASES.get(key)
    if iata:
        return CITIES[iata]
    return None


def city_name(iata: str) -> str:
    city = CITIES.get(iata.upper())
    return city.name_ru if city else iata.upper()


def city_photo(iata: str) -> str:
    city = CITIES.get(iata.upper())
    if city and city.photo_url:
        return city.photo_url
    return f"https://picsum.photos/seed/{iata.lower()}-travel/800/500"
