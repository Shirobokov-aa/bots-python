from aiogram import Dispatcher

from app.bot.handlers import router
from app.bot.middleware import DbMiddleware


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher()
    dp.update.middleware(DbMiddleware())
    dp.include_router(router)
    return dp
