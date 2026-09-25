from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, ChatMemberAdministrator, ChatMemberOwner, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import texts
from app.bot.keyboards import dest_pick_kb, main_kb, source_label_kb
from app.config import get_settings
from app.db.models import User
from app.services.parse_source import parse_channel, parse_invite, private_source_slug
from app.services.routes import (
    add_destination,
    add_route,
    add_source,
    add_source_by_chat_id,
    delete_route,
    get_destination,
    list_destinations,
    list_routes,
    list_sources,
    toggle_route,
    toggle_source_label,
)
from app.services.telethon_listener import get_listener

router = Router()

NAV_BUTTONS = {"Цели", "Источники", "Маршруты", "Помощь", "Приватный источник"}


class AddSource(StatesGroup):
    waiting_dest = State()
    waiting_source_label = State()


class AddPrivateSource(StatesGroup):
    waiting_bind = State()
    waiting_dest = State()
    waiting_source_label = State()


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


def _forward_channel(message: Message):
    chat = message.forward_from_chat
    if chat is not None and getattr(chat, "type", None) == "channel":
        return chat
    fo = getattr(message, "forward_origin", None)
    if fo is not None and getattr(fo, "type", None) == "channel":
        chat = getattr(fo, "chat", None)
        if chat is not None and getattr(chat, "type", None) == "channel":
            return chat
    return None


async def _ask_dest_for_pending(message: Message, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    dests = await list_destinations(session, db_user.id)
    if not dests:
        await state.clear()
        await message.answer("Сначала добавь цель: перешли пост из своего канала.")
        return
    data = await state.get_data()
    label = data.get("source_title") or data.get("source_username") or data.get("source_chat_id")
    await state.set_state(AddPrivateSource.waiting_dest)
    await message.answer(
        f"Источник {label}. Куда публиковать?",
        reply_markup=dest_pick_kb(dests),
    )


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
    await message.answer(texts.HELP, reply_markup=main_kb())


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Ок, отменил.", reply_markup=main_kb())


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
        await message.answer(
            "Источников нет. Публичный: @channel. Приватный: кнопка «Приватный источник»."
        )
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


@router.message(F.text == "Приватный источник")
async def cmd_private_source(message: Message, state: FSMContext, db_user: User) -> None:
    if await _deny_if_needed(message, db_user):
        return
    await state.set_state(AddPrivateSource.waiting_bind)
    await message.answer(texts.PRIVATE_SOURCE_HINT)


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
    await session.commit()
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
    await session.commit()
    await get_listener().refresh_watchlist()
    if route is None:
        await message.answer("Не найден.")
        return
    await message.answer(f"Маршрут #{route.id}: {'on' if route.is_active else 'off'}")


@router.message(Command("toggle_source"))
async def cmd_toggle_source(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    db_user: User,
) -> None:
    if await _deny_if_needed(message, db_user):
        return
    if not command.args or not command.args.strip().isdigit():
        await message.answer("Формат: /toggle_source 3")
        return
    route = await toggle_source_label(session, db_user.id, int(command.args.strip()))
    await session.commit()
    if route is None:
        await message.answer("Не найден.")
        return
    mode = "с источником" if route.show_source_label else "без источника (silent)"
    await message.answer(f"Маршрут #{route.id}: {mode}\n{texts.route_line(route)}")


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
    if seconds < 0:
        await message.answer("Секунды >= 0 (0 = без паузы, сразу).")
        return
    routes = await list_routes(session, db_user.id)
    route = next((r for r in routes if r.id == route_id), None)
    if route is None:
        await message.answer("Не найден.")
        return
    route.interval_seconds = seconds
    label = "без паузы" if seconds == 0 else f"каждые {seconds}s"
    await message.answer(f"Маршрут #{route.id}: {label}")


async def _register_forwarded_destination(message: Message, bot: Bot, session: AsyncSession, db_user: User) -> bool:
    """If message is forward from a channel and bot is admin there — register dest."""
    chat = _forward_channel(message)
    if chat is None:
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


async def _bind_private_from_forward(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    db_user: User,
) -> bool:
    chat = _forward_channel(message)
    if chat is None:
        return False
    listener = get_listener()
    resolved = await listener.resolve_chat(chat.id)
    if resolved is None:
        await message.answer(
            "Telethon-аккаунт не видит этот канал.\n"
            "Вступи им в канал или пришли инвайт https://t.me/+XXXX"
        )
        return True
    peer_id, title, uname = resolved
    await state.update_data(
        source_chat_id=peer_id,
        source_title=title or chat.title,
        source_username=uname or private_source_slug(peer_id),
    )
    await _ask_dest_for_pending(message, state, session, db_user)
    return True


@router.message(F.forward_from_chat | F.forward_origin)
async def on_forward(message: Message, bot: Bot, session: AsyncSession, db_user: User, state: FSMContext) -> None:
    if await _deny_if_needed(message, db_user):
        return
    current = await state.get_state()
    if current == AddPrivateSource.waiting_bind.state:
        handled = await _bind_private_from_forward(message, state, session, db_user)
        if not handled:
            await message.answer("Перешли пост из приватного канала-источника.")
        return
    handled = await _register_forwarded_destination(message, bot, session, db_user)
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
    dest = await get_destination(session, db_user.id, int(raw))
    if dest is None:
        await callback.answer("Цель не найдена", show_alert=True)
        return
    if not data.get("source_username") and data.get("source_chat_id") is None:
        await state.clear()
        await callback.answer("Сессия сброшена, начни снова", show_alert=True)
        return

    await state.update_data(dest_id=dest.id)
    current = await state.get_state()
    if current == AddPrivateSource.waiting_dest.state:
        await state.set_state(AddPrivateSource.waiting_source_label)
    else:
        await state.set_state(AddSource.waiting_source_label)
    await callback.message.edit_text(texts.SOURCE_LABEL_ASK, reply_markup=source_label_kb())
    await callback.answer()


@router.callback_query(F.data.startswith("src_label:"))
async def on_source_label(callback: CallbackQuery, state: FSMContext, session: AsyncSession, db_user: User) -> None:
    if not _is_admin(db_user.telegram_id):
        await callback.answer("Нет доступа", show_alert=True)
        return
    raw = (callback.data or "").split(":", 1)[-1]
    if raw == "cancel":
        await state.clear()
        await callback.message.edit_text("Отменил.")
        await callback.answer()
        return
    if raw not in {"0", "1"}:
        await callback.answer("bad")
        return

    data = await state.get_data()
    dest_id = data.get("dest_id")
    if dest_id is None:
        await state.clear()
        await callback.answer("Сессия сброшена, начни снова", show_alert=True)
        return
    dest = await get_destination(session, db_user.id, int(dest_id))
    if dest is None:
        await state.clear()
        await callback.answer("Цель не найдена", show_alert=True)
        return

    chat_id = data.get("source_chat_id")
    username = data.get("source_username")
    title = data.get("source_title")
    if chat_id is not None:
        source = await add_source_by_chat_id(
            session,
            db_user.id,
            chat_id=int(chat_id),
            title=title,
            username=username,
        )
    elif username:
        source = await add_source(session, db_user.id, username, title=title)
    else:
        await state.clear()
        await callback.answer("Сессия сброшена, начни снова", show_alert=True)
        return

    show_label = raw == "1"
    route = await add_route(
        session,
        db_user.id,
        source.id,
        dest.id,
        show_source_label=show_label,
    )
    await session.commit()
    # reload with relations for route_line
    routes = await list_routes(session, db_user.id)
    route = next((r for r in routes if r.id == route.id), route)
    await state.clear()
    await get_listener().refresh_watchlist()
    mode = "с источником" if show_label else "без источника"
    await callback.message.edit_text(f"Маршрут готов ({mode}):\n{texts.route_line(route)}")
    await callback.answer()


@router.message(AddPrivateSource.waiting_bind, F.text)
async def on_private_bind_text(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    db_user: User,
) -> None:
    if await _deny_if_needed(message, db_user):
        return
    if message.text in NAV_BUTTONS:
        return
    invite = parse_invite(message.text or "")
    if invite is None:
        await message.answer("Нужен forward из канала или инвайт https://t.me/+XXXX")
        return
    listener = get_listener()
    try:
        peer_id, title, uname = await listener.join_invite(invite.hash)
    except Exception as exc:
        await message.answer(f"Не смог вступить по инвайту: {exc}")
        return
    await state.update_data(
        source_chat_id=peer_id,
        source_title=title,
        source_username=uname or private_source_slug(peer_id),
    )
    await _ask_dest_for_pending(message, state, session, db_user)


@router.message(F.text)
async def on_text(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    db_user: User,
) -> None:
    if await _deny_if_needed(message, db_user):
        return
    if message.text in NAV_BUTTONS:
        return
    # invite typed outside private flow → hint
    invite = parse_invite(message.text or "")
    if invite is not None:
        await state.set_state(AddPrivateSource.waiting_bind)
        await on_private_bind_text(message, state, session, db_user)
        return
    parsed = parse_channel(message.text or "")
    if parsed is None:
        await message.answer(
            "Не похоже на канал. Пример: @durov или кнопка «Приватный источник»."
        )
        return
    dests = await list_destinations(session, db_user.id)
    if not dests:
        await message.answer("Сначала добавь цель: перешли пост из своего канала.")
        return
    await state.set_state(AddSource.waiting_dest)
    await state.update_data(source_username=parsed.username, source_chat_id=None, source_title=None)
    await message.answer(
        f"Источник {parsed.display}. Куда публиковать?",
        reply_markup=dest_pick_kb(dests),
    )
