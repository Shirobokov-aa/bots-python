from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.handlers import router
from app.bot.middleware import DbMiddleware


def build_dispatcher() -> Dispatcher:
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(DbMiddleware())
    dp.include_router(router)
    return dp
