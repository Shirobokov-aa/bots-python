from __future__ import annotations

import logging

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, URLInputFile

from app.services.deals import deal_photo, flight_caption, hotel_caption, tour_caption
from app.services.travelpayouts import FlightDeal, HotelDeal, TourDeal

log = logging.getLogger("traveldeals.channel")


def _caption(deal: FlightDeal | HotelDeal | TourDeal) -> str:
    if isinstance(deal, TourDeal):
        return tour_caption(deal)
    if isinstance(deal, HotelDeal):
        return hotel_caption(deal)
    return flight_caption(deal)


def _link(deal: FlightDeal | HotelDeal | TourDeal) -> str:
    if isinstance(deal, TourDeal):
        return deal.flight.link
    return deal.link


def deal_keyboard(deal: FlightDeal | HotelDeal | TourDeal) -> InlineKeyboardMarkup:
    if isinstance(deal, TourDeal):
        rows = [
            [InlineKeyboardButton(text="Билеты", url=deal.flight.link)],
            [InlineKeyboardButton(text="Отель", url=deal.hotel.link)],
        ]
    else:
        label = "Открыть отель" if isinstance(deal, HotelDeal) else "Открыть билеты"
        rows = [[InlineKeyboardButton(text=label, url=deal.link)]]
    return InlineKeyboardMarkup(inline_keyboard=rows)


async def post_deal_photo(
    bot: Bot,
    chat_id: int,
    deal: FlightDeal | HotelDeal | TourDeal,
) -> bool:
    caption = _caption(deal)
    if len(caption) > 1024:
        caption = caption[:1000] + "…"
    photo_url = deal_photo(deal)
    try:
        await bot.send_photo(
            chat_id,
            photo=URLInputFile(photo_url),
            caption=caption,
            parse_mode=ParseMode.HTML,
            reply_markup=deal_keyboard(deal),
        )
        return True
    except TelegramAPIError as exc:
        log.warning("send_photo fail, fallback text: %s", exc)
        try:
            await bot.send_message(
                chat_id,
                caption + f'\n\n<a href="{photo_url}">фото</a>',
                parse_mode=ParseMode.HTML,
                reply_markup=deal_keyboard(deal),
                disable_web_page_preview=False,
            )
            return True
        except TelegramAPIError as exc2:
            log.error("send_message fail: %s", exc2)
            return False


async def send_deal_dm(bot: Bot, telegram_id: int, deal: FlightDeal | HotelDeal | TourDeal) -> None:
    await post_deal_photo(bot, telegram_id, deal)
