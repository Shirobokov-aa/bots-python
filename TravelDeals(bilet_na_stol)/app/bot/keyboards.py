from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.services.hotel_links import HotelDeeplink
from app.services.travelpayouts import FlightDeal


def main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✈️ Билеты"), KeyboardButton(text="🏨 Отели")],
            [KeyboardButton(text="🧳 Тур"), KeyboardButton(text="🔔 Алерт")],
            [KeyboardButton(text="Помощь")],
        ],
        resize_keyboard=True,
    )


def flight_results_kb(deals: list[FlightDeal]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"{d.price} ₽ · {d.depart_date}", url=d.link)] for d in deals[:5]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def hotel_deeplink_kb(offer: HotelDeeplink) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="Отели на Островке", url=offer.ostrovok_url)],
        [InlineKeyboardButton(text="Отели на Яндекс Путешествиях", url=offer.yandex_url)],
    ]
    if offer.otello_url:
        rows.append([InlineKeyboardButton(text="Отели на Отелло (РФ)", url=offer.otello_url)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def tour_results_kb(
    flights: list[FlightDeal],
    hotel: HotelDeeplink | None = None,
) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"Билеты ~{f.price} ₽", url=f.link)] for f in flights[:3]
    ]
    if hotel:
        rows.append([InlineKeyboardButton(text="Отели на Островке", url=hotel.ostrovok_url)])
        rows.append([InlineKeyboardButton(text="Отели на Яндекс Путешествиях", url=hotel.yandex_url)])
        if hotel.otello_url:
            rows.append([InlineKeyboardButton(text="Отели на Отелло (РФ)", url=hotel.otello_url)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def flight_channel_kb(deal: FlightDeal, hotel: HotelDeeplink | None = None) -> InlineKeyboardMarkup:
    rows = [[InlineKeyboardButton(text="Открыть билеты", url=deal.link)]]
    if hotel:
        rows.append([InlineKeyboardButton(text="Отели на Островке", url=hotel.ostrovok_url)])
        rows.append([InlineKeyboardButton(text="Отели на Яндекс Путешествиях", url=hotel.yandex_url)])
        if hotel.otello_url:
            rows.append([InlineKeyboardButton(text="Отели на Отелло (РФ)", url=hotel.otello_url)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def alerts_kb(alert_ids: list[int]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"Выкл #{aid}", callback_data=f"alert_off:{aid}")]
        for aid in alert_ids
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
