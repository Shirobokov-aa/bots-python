from app.config import get_settings
from app.services.cities import CITIES


def start_text() -> str:
    channel = get_settings().channel_link
    ch_line = f"\nКанал горящих: {channel}" if channel else ""
    return (
        "<b>TravelDeals</b> — дешёвые авиа, отели и комбо-туры.\n\n"
        "Команды:\n"
        "/flight — поиск билетов\n"
        "/hotel — поиск отелей\n"
        "/tour — авиа + отель\n"
        "/alert — алерт по цене\n"
        "/alerts — мои алерты\n"
        "/cancel — отмена диалога\n"
        f"{ch_line}"
    )


def help_text() -> str:
    cities = ", ".join(sorted(CITIES.keys()))
    return (
        "Города можно писать по-русски или IATA.\n"
        f"Известные коды: {cities}\n\n"
        "Алерты: /alert → откуда → куда → макс. цена в ₽.\n"
        "Админ: /post_now — сразу прогнать посты в канал."
    )


def unknown_city() -> str:
    return "Не понял город. Пример: Москва, Сочи, AYT, DXB. /cancel"


def need_token() -> str:
    return "Travelpayouts token не задан в .env — поиск недоступен."
