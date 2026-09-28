from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.types import URLInputFile

from app.bot.keyboards import flight_channel_kb
from app.services.deals import deal_photo, flight_caption
from app.services.hotel_links import (
    HotelDeeplink,
    build_hotel_deeplink,
    hotel_dates_for_flight,
    wrap_hotel_deeplink,
)
from app.services.travelpayouts import FlightDeal

log = logging.getLogger("traveldeals.channel")


async def post_deal_photo(
    bot: Bot,
    chat_id: int,
    deal: FlightDeal,
    hotel: HotelDeeplink | None = None,
) -> bool:
    caption = flight_caption(deal)
    if hotel:
        caption += (
            f"\n\nОтели на даты поездки ({hotel.check_in} → {hotel.check_out}) — кнопки ниже."
        )
    if len(caption) > 1024:
        caption = caption[:1000] + "…"
    photo_url = deal_photo(deal)
    markup = flight_channel_kb(deal, hotel=hotel)
    try:
        await bot.send_photo(
            chat_id,
            photo=URLInputFile(photo_url),
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=markup,
        )
        return True
    except TelegramAPIError as exc:
        log.warning("send_photo fail, fallback text: %s", exc)
        try:
            await bot.send_message(
                chat_id,
                caption + f'\n\n<a href="{photo_url}">фото</a>',
                parse_mode=ParseMode.HTML,
                reply_markup=markup,
                disable_web_page_preview=False,
            )
            return True
        except TelegramAPIError as exc2:
            log.error("send_message fail: %s", exc2)
            return False


async def hotel_for_flight(deal: FlightDeal) -> HotelDeeplink | None:
    check_in, check_out = hotel_dates_for_flight(deal.depart_date, deal.return_date)
    offer = build_hotel_deeplink(deal.destination, check_in=check_in, check_out=check_out)
    if offer is None:
        return None
    return await wrap_hotel_deeplink(offer, sub_id="channel_hotel")


async def send_deal_dm(bot: Bot, telegram_id: int, deal: FlightDeal) -> None:
    await post_deal_photo(bot, telegram_id, deal)
