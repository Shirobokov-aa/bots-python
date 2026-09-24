from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser

from app.db.session import SessionLocal
from app.services.users import upsert_user


class DbMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        tg_user: TgUser | None = data.get("event_from_user")
        async with SessionLocal() as session:
            data["session"] = session
            if tg_user:
                data["db_user"] = await upsert_user(
                    session,
                    telegram_id=tg_user.id,
                    username=tg_user.username,
                    first_name=tg_user.first_name,
                )
            result = await handler(event, data)
            await session.commit()
            return result
