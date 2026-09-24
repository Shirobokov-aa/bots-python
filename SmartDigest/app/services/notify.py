from aiogram import Bot
from aiogram.enums import ParseMode

from app.utils.text import split_telegram


async def send_html(bot: Bot, chat_id: int, text: str, *, preview: bool = False) -> None:
    for chunk in split_telegram(text):
        await bot.send_message(
            chat_id,
            chunk,
            parse_mode=ParseMode.HTML,
            disable_web_page_preview=not preview,
        )
