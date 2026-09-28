from app.config import get_settings
from app.services.cities import CITIES


def start_text() -> str:
    channel = get_settings().channel_link
    ch_line = f"\nКанал: {channel}" if channel else ""
    return (
        "<b>Билет на стол</b> — спокойные подборки авиа с ценами "
        "и ссылки на поиск отелей у партнёров.\n\n"
        "Команды:\n"
        "/flight — билеты с ценой\n"
        "/hotel — поиск отелей (без цен в боте)\n"
        "/tour — билет + отели на те же даты\n"
        "/alert — алерт по цене билета\n"
        "/alerts — мои алерты\n"
        "/cancel — отмена\n"
        f"{ch_line}"
    )


def help_text() -> str:
    cities = ", ".join(sorted(CITIES.keys()))
    return (
        "Город: по-русски или IATA.\n"
        f"Коды: {cities}\n\n"
        "Отели: цены только на сайте партнёра (Островок / Яндекс). "
        "В канале и /tour даты отеля совпадают с вылетом.\n"
        "Алерт: /alert → откуда → куда → макс. цена в ₽.\n"
        "Админ: /post_now — пост в канал."
    )


def unknown_city() -> str:
    return "Не понял город. Пример: Москва, Сочи, AYT, DXB. /cancel"


def need_token() -> str:
    return "Travelpayouts token не задан в .env — поиск недоступен."
