from __future__ import annotations

from datetime import date, timedelta

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import texts
from app.bot.keyboards import (
    alerts_kb,
    flight_results_kb,
    hotel_deeplink_kb,
    main_kb,
    tour_results_kb,
)
from app.config import get_settings
from app.db.models import User
from app.services.alerts import add_alert, deactivate_alert, list_alerts
from app.services.cities import city_name, resolve_city
from app.services.deals import flight_caption
from app.services.hotel_links import (
    build_hotel_deeplink,
    hotel_dates_for_flight,
    wrap_hotel_deeplink,
)
from app.services.scheduler import run_deal_tick
from app.services.travelpayouts import get_tp_client

router = Router()


class FlightForm(StatesGroup):
    origin = State()
    destination = State()
    flexible = State()


class HotelForm(StatesGroup):
    city = State()
    nights = State()


class TourForm(StatesGroup):
    origin = State()
    destination = State()


class AlertForm(StatesGroup):
    origin = State()
    destination = State()
    max_price = State()


def _is_admin(telegram_id: int) -> bool:
    return telegram_id in get_settings().admin_ids


def _parse_nights(text: str) -> int | None:
    text = text.strip().lower().replace("ночей", "").replace("ночи", "").replace("ночь", "").strip()
    if text.isdigit():
        n = int(text)
        if 1 <= n <= 30:
            return n
    return None


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.start_text(), reply_markup=main_kb())


@router.message(Command("help"))
@router.message(F.text == "Помощь")
async def cmd_help(message: Message) -> None:
    await message.answer(texts.help_text())


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Ок, отменил.", reply_markup=main_kb())


@router.message(Command("flight"))
@router.message(F.text == "✈️ Билеты")
async def flight_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(FlightForm.origin)
    await message.answer("Откуда летим? (Москва / MOW)")


@router.message(FlightForm.origin)
async def flight_origin(message: Message, state: FSMContext) -> None:
    city = resolve_city(message.text or "")
    if not city:
        await message.answer(texts.unknown_city())
        return
    await state.update_data(origin=city.iata)
    await state.set_state(FlightForm.destination)
    await message.answer("Куда?")


@router.message(FlightForm.destination)
async def flight_destination(message: Message, state: FSMContext) -> None:
    city = resolve_city(message.text or "")
    if not city:
        await message.answer(texts.unknown_city())
        return
    await state.update_data(destination=city.iata)
    await state.set_state(FlightForm.flexible)
    await message.answer("Гибкие даты на месяц? Напиши «да» или дату YYYY-MM-DD")


@router.message(FlightForm.flexible)
async def flight_search(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.clear()
    if not get_settings().travelpayouts_token:
        await message.answer(texts.need_token())
        return

    origin = data["origin"]
    dest = data["destination"]
    raw = (message.text or "").strip().lower()
    client = get_tp_client()
    await message.answer("Ищу…")

    if raw in {"да", "yes", "y", "гибко", "месяц"}:
        deals = await client.latest_flights(origin, dest, limit=5)
    else:
        try:
            day = date.fromisoformat(raw[:10])
            month = day.strftime("%Y-%m")
        except ValueError:
            month = date.today().strftime("%Y-%m")
        deals = await client.calendar_flights(origin, dest, month)
        deals = deals[:5] or await client.latest_flights(origin, dest, limit=5)

    if not deals:
        await message.answer("Ничего не нашёл. Попробуй другой маршрут.")
        return

    lines = [flight_caption(d) for d in deals[:3]]
    await message.answer(
        "\n\n—\n\n".join(lines),
        reply_markup=flight_results_kb(deals),
        disable_web_page_preview=True,
    )


@router.message(Command("hotel"))
@router.message(F.text == "🏨 Отели")
async def hotel_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(HotelForm.city)
    await message.answer("Город отеля? (Анталья / AYT)")


@router.message(HotelForm.city)
async def hotel_city(message: Message, state: FSMContext) -> None:
    city = resolve_city(message.text or "")
    if not city:
        await message.answer(texts.unknown_city())
        return
    await state.update_data(city=city.iata)
    await state.set_state(HotelForm.nights)
    await message.answer("Сколько ночей? (число 1–30)")


@router.message(HotelForm.nights)
async def hotel_search(message: Message, state: FSMContext) -> None:
    nights = _parse_nights(message.text or "")
    if nights is None:
        await message.answer("Нужно число ночей, например 7")
        return
    data = await state.get_data()
    await state.clear()

    offer = build_hotel_deeplink(data["city"], nights=nights)
    if offer is None:
        await message.answer(texts.unknown_city())
        return
    offer = await wrap_hotel_deeplink(offer, sub_id="bot_hotel")
    await message.answer(
        (
            f"<b>Отели · {city_name(offer.city_iata)}</b>\n"
            f"{offer.check_in} → {offer.check_out} · {offer.nights} ноч.\n\n"
            "Цены смотри на сайте партнёра — кнопки ниже."
        ),
        reply_markup=hotel_deeplink_kb(offer),
        disable_web_page_preview=True,
    )


@router.message(Command("tour"))
@router.message(F.text == "🧳 Тур")
async def tour_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(TourForm.origin)
    await message.answer("Тур = билет + отель. Откуда вылет?")


@router.message(TourForm.origin)
async def tour_origin(message: Message, state: FSMContext) -> None:
    city = resolve_city(message.text or "")
    if not city:
        await message.answer(texts.unknown_city())
        return
    await state.update_data(origin=city.iata)
    await state.set_state(TourForm.destination)
    await message.answer("Куда (город отдыха)?")


@router.message(TourForm.destination)
async def tour_search(message: Message, state: FSMContext) -> None:
    city = resolve_city(message.text or "")
    if not city:
        await message.answer(texts.unknown_city())
        return
    data = await state.get_data()
    await state.clear()
    if not get_settings().travelpayouts_token:
        await message.answer(texts.need_token())
        return

    origin = data["origin"]
    dest = city.iata
    await message.answer("Собираю комбо…")
    flights = await get_tp_client().latest_flights(origin, dest, limit=5)
    if not flights:
        await message.answer("Билетов не нашёл. Попробуй /flight отдельно.")
        return

    top = flights[:2]
    check_in, check_out = hotel_dates_for_flight(top[0].depart_date, top[0].return_date)
    hotel = build_hotel_deeplink(dest, check_in=check_in, check_out=check_out)
    if hotel:
        hotel = await wrap_hotel_deeplink(hotel, sub_id="bot_tour")

    lines = [flight_caption(f) for f in top]
    hotel_line = ""
    if hotel:
        hotel_line = (
            f"\n\nОтели в {city_name(dest)} на даты первого варианта "
            f"({hotel.check_in} → {hotel.check_out}) — кнопки ниже."
        )
    await message.answer(
        "<b>Билет + отель</b>\n\n" + "\n\n—\n\n".join(lines) + hotel_line,
        reply_markup=tour_results_kb(top, hotel=hotel),
        disable_web_page_preview=True,
    )


@router.message(Command("alert"))
@router.message(F.text == "🔔 Алерт")
async def alert_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(AlertForm.origin)
    await message.answer("Алерт: откуда?")


@router.message(AlertForm.origin)
async def alert_origin(message: Message, state: FSMContext) -> None:
    city = resolve_city(message.text or "")
    if not city:
        await message.answer(texts.unknown_city())
        return
    await state.update_data(origin=city.iata)
    await state.set_state(AlertForm.destination)
    await message.answer("Куда?")


@router.message(AlertForm.destination)
async def alert_destination(message: Message, state: FSMContext) -> None:
    city = resolve_city(message.text or "")
    if not city:
        await message.answer(texts.unknown_city())
        return
    await state.update_data(destination=city.iata)
    await state.set_state(AlertForm.max_price)
    await message.answer("Макс. цена билета в ₽? (число)")


@router.message(AlertForm.max_price)
async def alert_save(message: Message, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    raw = (message.text or "").replace(" ", "").replace("₽", "")
    if not raw.isdigit():
        await message.answer("Нужно число, например 12000")
        return
    max_price = int(raw)
    data = await state.get_data()
    await state.clear()
    alert = await add_alert(session, db_user, data["origin"], data["destination"], max_price)
    await message.answer(
        f"Алерт #{alert.id}: {city_name(alert.origin)} → {city_name(alert.destination)} "
        f"до {alert.max_price} ₽. Список: /alerts",
        reply_markup=main_kb(),
    )


@router.message(Command("alerts"))
async def cmd_alerts(message: Message, session: AsyncSession, db_user: User) -> None:
    alerts = await list_alerts(session, db_user.id)
    active = [a for a in alerts if a.is_active]
    if not active:
        await message.answer("Активных алертов нет. /alert")
        return
    lines = [
        f"#{a.id} {city_name(a.origin)} → {city_name(a.destination)} ≤ {a.max_price} ₽"
        for a in active
    ]
    await message.answer("\n".join(lines), reply_markup=alerts_kb([a.id for a in active]))


@router.callback_query(F.data.startswith("alert_off:"))
async def alert_off(query: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    alert_id = int(query.data.split(":")[1])
    ok = await deactivate_alert(session, db_user.id, alert_id)
    await query.answer("Выключен" if ok else "Не найден")
    if query.message:
        await query.message.answer(f"Алерт #{alert_id} выключен." if ok else "Алерт не найден.")


@router.message(Command("post_now"))
async def cmd_post_now(message: Message, db_user: User) -> None:
    if not _is_admin(db_user.telegram_id):
        await message.answer("Нет прав.")
        return
    await message.answer("Гоню воркер…")
    n = await run_deal_tick(message.bot)
    await message.answer(f"Готово. Постов в канал: {n}")
