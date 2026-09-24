from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.db.models import Source


def main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Источники"), KeyboardButton(text="Дайджест")],
            [KeyboardButton(text="Время"), KeyboardButton(text="Помощь")],
            [KeyboardButton(text="VIP")],
        ],
        resize_keyboard=True,
    )


def source_kb(source: Source) -> InlineKeyboardMarkup:
    pause_label = "Пауза" if source.is_active else "Включить"
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text=pause_label, callback_data=f"s:toggle:{source.id}"),
        InlineKeyboardButton(text="Обновить", callback_data=f"s:fetch:{source.id}"),
    )
    builder.row(InlineKeyboardButton(text="Удалить", callback_data=f"s:del:{source.id}"))
    return builder.as_markup()


def confirm_delete_kb(source_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Точно удалить", callback_data=f"s:delok:{source_id}"),
                InlineKeyboardButton(text="Отмена", callback_data="s:cancel"),
            ]
        ]
    )
