from __future__ import annotations

import re

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot import texts
from app.bot.keyboards import confirm_delete_kb, main_kb, source_kb
from app.config import get_settings
from app.db.models import Source, User
from app.ingest import fetch_parsed
from app.ingest.parse_source import parse_source
from app.services.collector import apply_fetch, persist_fetch
from app.services.scheduler import render_user_digest
from app.services.sources import (
    DuplicateSourceError,
    SourceLimitError,
    add_source,
    delete_source,
    get_user_source,
    interval_for,
    list_sources,
    toggle_source,
)
from app.services.notify import send_html

router = Router()
HOUR_RE = re.compile(r"^(\d{1,2})(?::(\d{2}))?$")


class SetTime(StatesGroup):
    waiting_hour = State()


def _is_admin(telegram_id: int) -> bool:
    return telegram_id in get_settings().admin_ids


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(texts.start_text(), reply_markup=main_kb())


@router.message(Command("help"))
@router.message(F.text == "Помощь")
async def cmd_help(message: Message) -> None:
    await message.answer(texts.help_text())


@router.message(Command("vip"))
@router.message(F.text == "VIP")
async def cmd_vip(message: Message, db_user: User) -> None:
    await message.answer(texts.vip_text(db_user.is_vip))


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Ок, отменил.")


@router.message(Command("grant_vip"))
async def cmd_grant_vip(message: Message, command: CommandObject, session: AsyncSession, db_user: User) -> None:
    if not _is_admin(db_user.telegram_id):
        await message.answer("Нет прав.")
        return
    if not command.args or not command.args.strip().isdigit():
        await message.answer("Формат: /grant_vip 123456789")
        return
    target_id = int(command.args.strip())
    result = await session.execute(select(User).where(User.telegram_id == target_id))
    target = result.scalar_one_or_none()
    if target is None:
        await message.answer("Пользователь ещё не писал боту.")
        return
    target.is_vip = True
    for source in await list_sources(session, target.id):
        source.interval_seconds = interval_for(target)
    await message.answer(f"VIP выдан {target_id}")


@router.message(Command("sources"))
@router.message(Command("list"))
@router.message(F.text == "Источники")
async def cmd_sources(message: Message, session: AsyncSession, db_user: User) -> None:
    sources = await list_sources(session, db_user.id)
    if not sources:
        await message.answer("Пока пусто. Пришли RSS, сайт или @канал.")
        return
    for source in sources:
        await message.answer(texts.source_card(source), reply_markup=source_kb(source))


@router.message(Command("digest"))
@router.message(F.text == "Дайджест")
async def cmd_digest(message: Message, session: AsyncSession, db_user: User, bot: Bot) -> None:
    sources = await list_sources(session, db_user.id)
    if not sources:
        await message.answer("Пока нет источников. Пришли RSS, сайт или @канал.")
        return
    progress = await message.answer("Собираю выжимку…")
    text = await render_user_digest(session, db_user, allow_empty=True)
    if progress:
        try:
            await progress.delete()
        except TelegramBadRequest:
            pass
    if text:
        await send_html(bot, message.chat.id, text)


async def _set_digest_hour(message: Message, db_user: User, state: FSMContext, args: str) -> None:
    if args:
        hour = parse_hour(args)
        if hour is None:
            await message.answer("Час от 0 до 23, например 9 или 21:00.")
            return
        db_user.digest_hour = hour
        await message.answer(f"Буду присылать дайджест в {hour:02d}:00 ({get_settings().digest_timezone}).")
        return
    await state.set_state(SetTime.waiting_hour)
    await message.answer(texts.time_text(db_user.digest_hour))


@router.message(Command("time"))
async def cmd_time(message: Message, command: CommandObject, state: FSMContext, db_user: User) -> None:
    await _set_digest_hour(message, db_user, state, (command.args or "").strip())


@router.message(F.text == "Время")
async def cmd_time_btn(message: Message, state: FSMContext, db_user: User) -> None:
    await _set_digest_hour(message, db_user, state, "")


@router.message(SetTime.waiting_hour, F.text)
async def on_hour(message: Message, state: FSMContext, db_user: User) -> None:
    hour = parse_hour(message.text or "")
    if hour is None:
        await message.answer("Час от 0 до 23, например 9 или 21:00. Или /cancel")
        return
    db_user.digest_hour = hour
    await state.clear()
    await message.answer(f"Буду присылать дайджест в {hour:02d}:00 ({get_settings().digest_timezone}).")


@router.callback_query(F.data.startswith("s:toggle:"))
async def on_toggle(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    source = await _source_from_callback(callback, session, db_user)
    if source is None:
        return
    await toggle_source(session, source)
    await callback.answer("Пауза" if not source.is_active else "Снова читаю")
    if callback.message:
        await callback.message.edit_text(texts.source_card(source), reply_markup=source_kb(source))


@router.callback_query(F.data.startswith("s:del:"))
async def on_del(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    source = await _source_from_callback(callback, session, db_user)
    if source is None:
        return
    await callback.answer()
    if callback.message:
        await callback.message.edit_reply_markup(reply_markup=confirm_delete_kb(source.id))


@router.callback_query(F.data.startswith("s:delok:"))
async def on_del_ok(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    source = await _source_from_callback(callback, session, db_user)
    if source is None:
        return
    await delete_source(session, source)
    await callback.answer("Удалил")
    if callback.message:
        await callback.message.edit_text("Источник удалён.")


@router.callback_query(F.data == "s:cancel")
async def on_cancel_cb(callback: CallbackQuery) -> None:
    await callback.answer("Ок")


@router.callback_query(F.data.startswith("s:fetch:"))
async def on_fetch(callback: CallbackQuery, session: AsyncSession, db_user: User) -> None:
    source = await _source_from_callback(callback, session, db_user)
    if source is None:
        return
    try:
        await callback.answer("Обновляю…")
    except TelegramBadRequest:
        pass
    source.is_active = True
    source.consecutive_errors = 0
    try:
        await apply_fetch(session, source)
    except Exception as exc:
        source.last_error = str(exc)[:200]
    if callback.message:
        await callback.message.edit_text(texts.source_card(source), reply_markup=source_kb(source))


@router.message(F.text)
async def on_text(message: Message, session: AsyncSession, db_user: User) -> None:
    parsed = parse_source(message.text or "")
    if not parsed:
        await message.answer("Нужна ссылка http(s), RSS или @канал. Или /help")
        return
    progress = await message.answer("Смотрю источник…")
    result = await fetch_parsed(parsed)
    if result.error and not result.items:
        await progress.edit_text(f"Не вышло: {result.error}")
        return
    kind = result.kind or parsed.kind
    url = result.canonical_url or parsed.url
    try:
        source = await add_source(
            session,
            db_user,
            parsed,
            title=result.title or parsed.display,
            fetch_url=url,
            kind=kind,
        )
    except DuplicateSourceError as exc:
        await progress.edit_text(str(exc))
        return
    except SourceLimitError as exc:
        await progress.edit_text(str(exc) + "\nУдали лишнее в /sources или бери /vip")
        return
    added = await persist_fetch(session, source, result)
    extra = f"\nЗапомнил {added} материалов." if added else ""
    await progress.edit_text(texts.source_card(source) + extra, reply_markup=source_kb(source))


def parse_hour(text: str) -> int | None:
    match = HOUR_RE.match(text.strip())
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2) or "0")
    if minute != 0 or not 0 <= hour <= 23:
        return None
    return hour


async def _source_from_callback(callback: CallbackQuery, session: AsyncSession, db_user: User) -> Source | None:
    try:
        source_id = int((callback.data or "").rsplit(":", 1)[1])
    except (ValueError, IndexError):
        await callback.answer("Сломанная кнопка", show_alert=True)
        return None
    source = await get_user_source(session, db_user.id, source_id)
    if source is None:
        await callback.answer("Не твой источник", show_alert=True)
        return None
    return source
