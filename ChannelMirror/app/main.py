from __future__ import annotations

from contextlib import asynccontextmanager
import asyncio
from pathlib import Path
import logging

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Update
from fastapi import FastAPI, Header, HTTPException, Request

from app.bot import build_dispatcher
from app.config import get_settings
from app.db.session import init_db
from app.services.scheduler import scheduler_loop
from app.services.telethon_listener import get_listener

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
log = logging.getLogger("channelmirror")


def _ensure_dirs() -> None:
    Path("data").mkdir(exist_ok=True)
    Path(get_settings().media_dir).mkdir(parents=True, exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    if not settings.telegram_bot_token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN пустой")

    _ensure_dirs()
    await init_db()

    bot = Bot(settings.telegram_bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = build_dispatcher()
    stop = asyncio.Event()
    app.state.bot = bot
    app.state.dp = dp
    app.state.stop = stop

    listener = get_listener()
    await listener.start()

    sched_task = asyncio.create_task(scheduler_loop(bot, stop), name="scheduler")
    poll_task = None

    if settings.telegram_mode == "webhook":
        if not settings.telegram_webhook_url:
            raise RuntimeError("TELEGRAM_WEBHOOK_URL нужен для webhook")
        await bot.set_webhook(
            url=settings.telegram_webhook_url,
            secret_token=settings.telegram_webhook_secret,
            drop_pending_updates=False,
        )
        log.info("webhook %s", settings.telegram_webhook_url)
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        poll_task = asyncio.create_task(dp.start_polling(bot, drop_pending_updates=True), name="polling")
        log.info("polling on")

    try:
        yield
    finally:
        stop.set()
        await listener.stop()
        tasks = [sched_task]
        if poll_task:
            await dp.stop_polling()
            tasks.append(poll_task)
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)
        await bot.session.close()


app = FastAPI(title="ChannelMirror", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/telegram/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
) -> dict[str, bool]:
    settings = get_settings()
    if settings.telegram_mode != "webhook":
        raise HTTPException(404, "webhook off")
    if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
        raise HTTPException(401, "bad secret")
    payload = await request.json()
    update = Update.model_validate(payload, context={"bot": request.app.state.bot})
    await request.app.state.dp.feed_update(request.app.state.bot, update)
    return {"ok": True}
