from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, ChatMemberAdministrator, ChatMemberOwner, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import texts
from app.bot.keyboards import dest_pick_kb, main_kb
from app.config import get_settings
from app.db.models import User
from app.services.parse_source import parse_channel
from app.services.routes import (
    add_destination,
    add_route,
    add_source,
    delete_route,
    get_destination,
    list_destinations,
    list_routes,
    list_sources,
    toggle_route,
)
from app.services.telethon_listener import get_listener

router = Router()


class AddSource(StatesGroup):
    waiting_dest = State()


def _is_admin(telegram_id: int) -> bool:
    admins = get_settings().admin_ids
    if not admins:
        return True
    return telegram_id in admins


async def _deny_if_needed(message: Message, db_user: User) -> bool:
    if _is_admin(db_user.telegram_id):
        return False
    await message.answer("Доступ только админам (ADMIN_TELEGRAM_IDS).")
    return True


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext, db_user: User) -> None:
    await state.clear()
    if await _deny_if_needed(message, db_user):
        return
    await message.answer(texts.START, reply_markup=main_kb())


@router.message(Command("help"))
@router.message(F.text == "Помощь")
async def cmd_help(message: Message, db_user: User) -> None:
    if await _deny_if_needed(message, db_user):
        return
    await message.answer(texts.HELP)


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Ок, отменил.")


@router.message(Command("dests"))
@router.message(F.text == "Цели")
async def cmd_dests(message: Message, session: AsyncSession, db_user: User) -> None:
    if await _deny_if_needed(message, db_user):
        return
    dests = await list_destinations(session, db_user.id)
    if not dests:
        await message.answer("Целей нет. Перешли пост из своего канала (бот = админ).")
        return
    lines = ["Цели:"] + [texts.dest_line(d) for d in dests]
    await message.answer("\n".join(lines))


@router.message(Command("sources"))
@router.message(F.text == "Источники")
async def cmd_sources(message: Message, session: AsyncSession, db_user: User) -> None:
    if await _deny_if_needed(message, db_user):
        return
    sources = await list_sources(session, db_user.id)
    if not sources:
        await message.answer("Источников нет. Пришли @channel или https://t.me/channel")
        return
    lines = ["Источники:"] + [texts.source_line(s) for s in sources]
    await message.answer("\n".join(lines))


@router.message(Command("routes"))
@router.message(F.text == "Маршруты")
async def cmd_routes(message: Message, session: AsyncSession, db_user: User) -> None:
    if await _deny_if_needed(message, db_user):
        return
    routes = await list_routes(session, db_user.id)
    if not routes:
        await message.answer("Маршрутов нет. Пришли ссылку на источник.")
        return
    lines = ["Маршруты:"] + [texts.route_line(r) for r in routes]
    await message.answer("\n".join(lines))


@router.message(Command("del_route"))
async def cmd_del_route(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    db_user: User,
) -> None:
    if await _deny_if_needed(message, db_user):
        return
    if not command.args or not command.args.strip().isdigit():
        await message.answer("Формат: /del_route 3")
        return
    ok = await delete_route(session, db_user.id, int(command.args.strip()))
    await get_listener().refresh_watchlist()
    await message.answer("Удалил." if ok else "Не найден.")


@router.message(Command("toggle_route"))
async def cmd_toggle_route(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    db_user: User,
) -> None:
    if await _deny_if_needed(message, db_user):
        return
    if not command.args or not command.args.strip().isdigit():
        await message.answer("Формат: /toggle_route 3")
        return
    route = await toggle_route(session, db_user.id, int(command.args.strip()))
    await get_listener().refresh_watchlist()
    if route is None:
        await message.answer("Не найден.")
        return
    await message.answer(f"Маршрут #{route.id}: {'on' if route.is_active else 'off'}")


@router.message(Command("interval"))
async def cmd_interval(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    db_user: User,
) -> None:
    if await _deny_if_needed(message, db_user):
        return
    parts = (command.args or "").split()
    if len(parts) != 2 or not parts[0].isdigit() or not parts[1].isdigit():
        await message.answer("Формат: /interval ID СЕКУНДЫ  (напр. /interval 1 3600)")
        return
    route_id, seconds = int(parts[0]), int(parts[1])
    if seconds < 60:
        await message.answer("Минимум 60 секунд.")
        return
    routes = await list_routes(session, db_user.id)
    route = next((r for r in routes if r.id == route_id), None)
    if route is None:
        await message.answer("Не найден.")
        return
    route.interval_seconds = seconds
    await message.answer(f"Маршрут #{route.id}: каждые {seconds}s")


async def _register_forwarded_channel(message: Message, bot: Bot, session: AsyncSession, db_user: User) -> bool:
    """If message is forward from a channel and bot is admin there — register dest."""
    chat = message.forward_from_chat
    if chat is None or getattr(chat, "type", None) != "channel":
        # aiogram 3.7+ MessageOriginChannel
        fo = getattr(message, "forward_origin", None)
        if fo is not None and getattr(fo, "type", None) == "channel":
            chat = getattr(fo, "chat", None)
        if chat is None or getattr(chat, "type", None) != "channel":
            return False
    me = await bot.get_me()
    try:
        member = await bot.get_chat_member(chat.id, me.id)
    except Exception:
        await message.answer("Не могу проверить права в канале. Добавь бота админом.")
        return True
    if not isinstance(member, (ChatMemberAdministrator, ChatMemberOwner)):
        await message.answer("Бот должен быть админом канала с правом постить.")
        return True
    can_post = True
    if isinstance(member, ChatMemberAdministrator):
        can_post = bool(member.can_post_messages)
    if not can_post:
        await message.answer("Нужно право post_messages.")
        return True
    dest = await add_destination(
        session,
        db_user.id,
        chat_id=chat.id,
        title=chat.title,
        username=chat.username,
    )
    await message.answer(f"Цель сохранена: {texts.dest_line(dest)}")
    return True


@router.message(F.forward_from_chat | F.forward_origin)
async def on_forward(message: Message, bot: Bot, session: AsyncSession, db_user: User, state: FSMContext) -> None:
    if await _deny_if_needed(message, db_user):
        return
    handled = await _register_forwarded_channel(message, bot, session, db_user)
    if not handled:
        await message.answer("Перешли пост именно из канала-цели.")


@router.callback_query(F.data.startswith("pick_dest:"))
async def on_pick_dest(callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    if not _is_admin(db_user.telegram_id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    raw = (callback.data or "").split(":", 1)[-1]
    if raw == "cancel":
        await state.clear()
        await callback.message.edit_text("Отменил.")
        await callback.answer()
        return
    if not raw.isdigit():
        await callback.answer("bad id")
        return
    data = await state.get_data()
    username = data.get("source_username")
    if not username:
        await state.clear()
        await callback.answer("Сессия сброшена, пришли ссылку снова", show_alert=True)
        return
    dest = await get_destination(session, db_user.id, int(raw))
    if dest is None:
        await callback.answer("Цель не найдена", show_alert=True)
        return
    source = await add_source(session, db_user.id, username)
    route = await add_route(session, db_user.id, source.id, dest.id)
    await state.clear()
    await get_listener().refresh_watchlist()
    # TODO(ai): optional per-route AI profile (filter/rewrite)
    await callback.message.edit_text(f"Маршрут готов:\n{texts.route_line(route)}")
    await callback.answer()


@router.message(F.text)
async def on_text(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    db_user: User,
) -> None:
    if await _deny_if_needed(message, db_user):
        return
    if message.text in {"Цели", "Источники", "Маршруты", "Помощь"}:
        return
    parsed = parse_channel(message.text or "")
    if parsed is None:
        await message.answer("Не похоже на канал. Пример: @durov или https://t.me/durov")
        return
    dests = await list_destinations(session, db_user.id)
    if not dests:
        await message.answer("Сначала добавь цель: перешли пост из своего канала.")
        return
    await state.set_state(AddSource.waiting_dest)
    await state.update_data(source_username=parsed.username)
    await message.answer(
        f"Источник {parsed.display}. Куда публиковать?",
        reply_markup=dest_pick_kb(dests),
    )
