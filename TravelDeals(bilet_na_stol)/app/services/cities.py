from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class City:
    iata: str
    name_ru: str
    photo_url: str = ""
    # Ostrovok path after /hotel/ e.g. russia/moscow — None → fallback ?q=
    ostrovok_path: str | None = None
    # Yandex Travel geo slug: /hotels/{slug}/
    yandex_slug: str | None = None
    # Otello (RU only) path slug under otello.ru/hotels/
    otello_slug: str | None = None


def _c(
    iata: str,
    name_ru: str,
    *,
    ostrovok: str | None = None,
    yandex: str | None = None,
    otello: str | None = None,
) -> City:
    return City(
        iata,
        name_ru,
        f"https://picsum.photos/seed/{iata.lower()}-travel/800/500",
        ostrovok_path=ostrovok,
        yandex_slug=yandex,
        otello_slug=otello,
    )


# photo_url: picsum seeds (fallback для канала; P5 — нормальные фото позже)
CITIES: dict[str, City] = {
    # --- origins / РФ ---
    "MOW": _c("MOW", "Москва", ostrovok="russia/moscow", yandex="moscow", otello="moscow"),
    "LED": _c(
        "LED",
        "Санкт-Петербург",
        ostrovok=None,
        yandex="saint-petersburg",
        otello="saint-petersburg",
    ),
    "SVX": _c(
        "SVX",
        "Екатеринбург",
        ostrovok="russia/yekaterinburg",
        yandex="yekaterinburg",
        otello="yekaterinburg",
    ),
    "KZN": _c("KZN", "Казань", ostrovok="russia/kazan", yandex="kazan", otello="kazan"),
    "AER": _c("AER", "Сочи", ostrovok="russia/sochi", yandex="sochi", otello="sochi"),
    "KRR": _c(
        "KRR",
        "Краснодар",
        ostrovok="russia/krasnodar",
        yandex="krasnodar",
        otello="krasnodar",
    ),
    "OVB": _c(
        "OVB",
        "Новосибирск",
        ostrovok="russia/novosibirsk",
        yandex="novosibirsk",
        otello="novosibirsk",
    ),
    "UFA": _c("UFA", "Уфа", ostrovok="russia/ufa", yandex="ufa", otello="ufa"),
    "ROV": _c(
        "ROV",
        "Ростов-на-Дону",
        ostrovok="russia/rostov-on-don",
        yandex="rostov-on-don",
        otello="rostov-on-don",
    ),
    # --- popular destinations ---
    "AYT": _c("AYT", "Анталья", ostrovok="turkey/antalya", yandex="antalya"),
    "IST": _c("IST", "Стамбул", ostrovok="turkey/istanbul", yandex="istanbul"),
    "DXB": _c(
        "DXB",
        "Дубай",
        ostrovok="united_arab_emirates/dubai",
        yandex="dubai",
    ),
    "AUH": _c(
        "AUH",
        "Абу-Даби",
        ostrovok="united_arab_emirates/abu_dhabi",
        yandex="abu-dhabi",
    ),
    "BKK": _c("BKK", "Бангкок", ostrovok="thailand/bangkok", yandex="bangkok"),
    "HKT": _c("HKT", "Пхукет", ostrovok="thailand/phuket", yandex="phuket"),
    "EVN": _c("EVN", "Ереван", ostrovok="armenia/yerevan", yandex="yerevan"),
    "BUS": _c("BUS", "Батуми", ostrovok="georgia/batumi", yandex="batumi"),
    "TBS": _c("TBS", "Тбилиси", ostrovok="georgia/tbilisi", yandex="tbilisi"),
    "SSH": _c("SSH", "Шарм-эш-Шейх", ostrovok="egypt/sharm_el_sheikh", yandex="sharm-el-sheikh"),
    "HRG": _c("HRG", "Хургада", ostrovok="egypt/hurghada", yandex="hurghada"),
    "MLE": _c("MLE", "Мале", ostrovok="maldives/male", yandex="male"),
    "TIV": _c("TIV", "Тиват", ostrovok="montenegro/tivat", yandex="tivat"),
    "TGD": _c("TGD", "Подгорица", ostrovok="montenegro/podgorica", yandex="podgorica"),
    "PRG": _c("PRG", "Прага", ostrovok="czech_republic/prague", yandex="prague"),
    "BCN": _c("BCN", "Барселона", ostrovok="spain/barcelona", yandex="barcelona"),
    "ALA": _c("ALA", "Алматы", ostrovok="kazakhstan/almaty", yandex="almaty"),
    "NQZ": _c("NQZ", "Астана", ostrovok="kazakhstan/astana", yandex="astana"),
    "MSQ": _c("MSQ", "Минск", ostrovok="belarus/minsk", yandex="minsk"),
    "RIX": _c("RIX", "Рига", ostrovok="latvia/riga", yandex="riga"),
    "HEL": _c("HEL", "Хельсинки", ostrovok="finland/helsinki", yandex="helsinki"),
    "DPS": _c("DPS", "Денпасар", ostrovok="indonesia/denpasar", yandex="denpasar"),
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
    "краснодар": "KRR",
    "новосибирск": "OVB",
    "нск": "OVB",
    "уфа": "UFA",
    "ростов": "ROV",
    "ростов-на-дону": "ROV",
    "анталья": "AYT",
    "анталия": "AYT",
    "аналья": "AYT",
    "стамбул": "IST",
    "дубай": "DXB",
    "абу-даби": "AUH",
    "абу даби": "AUH",
    "бангкок": "BKK",
    "пхукет": "HKT",
    "ереван": "EVN",
    "батуми": "BUS",
    "тбилиси": "TBS",
    "шарм": "SSH",
    "шарм-эль-шейх": "SSH",
    "шарм-эш-шейх": "SSH",
    "хургада": "HRG",
    "мале": "MLE",
    "мальдивы": "MLE",
    "тиват": "TIV",
    "черногория": "TIV",
    "подгорица": "TGD",
    "прага": "PRG",
    "барселона": "BCN",
    "алматы": "ALA",
    "астана": "NQZ",
    "нур-султан": "NQZ",
    "минск": "MSQ",
    "рига": "RIX",
    "хельсинки": "HEL",
    "бали": "DPS",
    "денпасар": "DPS",
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
