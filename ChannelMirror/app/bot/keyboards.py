from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


def main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Цели"), KeyboardButton(text="Источники")],
            [KeyboardButton(text="Приватный источник")],
            [KeyboardButton(text="Маршруты"), KeyboardButton(text="Помощь")],
        ],
        resize_keyboard=True,
    )


def dest_pick_kb(destinations: list) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text=(d.title or d.username or str(d.chat_id))[:40],
                callback_data=f"pick_dest:{d.id}",
            )
        ]
        for d in destinations
    ]
    rows.append([InlineKeyboardButton(text="Отмена", callback_data="pick_dest:cancel")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def source_label_kb() -> InlineKeyboardMarkup:
    """Optional plain-text attribution: Источник: \"Title\"."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="С источником", callback_data="src_label:1")],
            [InlineKeyboardButton(text="Без источника", callback_data="src_label:0")],
            [InlineKeyboardButton(text="Отмена", callback_data="src_label:cancel")],
        ]
    )
