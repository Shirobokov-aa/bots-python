from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup

from app.services.travelpayouts import FlightDeal, HotelDeal, TourDeal


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


def hotel_results_kb(deals: list[HotelDeal]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"{d.price} ₽/ночь · {d.hotel_name[:28]}", url=d.link)]
        for d in deals[:5]
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)


def tour_results_kb(deals: list[TourDeal]) -> InlineKeyboardMarkup:
    rows = []
    for d in deals[:3]:
        rows.append([InlineKeyboardButton(text=f"Билеты ~{d.flight.price} ₽", url=d.flight.link)])
        rows.append([InlineKeyboardButton(text=f"Отель ~{d.hotel.price} ₽/н", url=d.hotel.link)])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def alerts_kb(alert_ids: list[int]) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text=f"Выкл #{aid}", callback_data=f"alert_off:{aid}")]
        for aid in alert_ids
    ]
    return InlineKeyboardMarkup(inline_keyboard=rows)
