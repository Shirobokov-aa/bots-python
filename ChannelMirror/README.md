# ChannelMirror

Silent copy: открытые TG-источники → твои каналы. Без атрибуции источника. ИИ позже (`# TODO(ai)`).

## MVP

1. Бот админ в целевом канале → перешли пост из канала в бота.
2. Пришли `@source` / `https://t.me/source` → выбери цель.
3. Публичный источник: `@source` / `https://t.me/source` → выбери цель.
4. Приватный: кнопка **Приватный источник** → forward поста или инвайт `t.me/+…`
   (Telethon-аккаунт должен быть / стать участником).
5. Telethon слушает источники, очередь, публикация раз в `POST_INTERVAL_SECONDS` (дефолт 5400 ≈ 1.5 ч).
6. Пост уходит как «свой» (не forward).

## Setup

```bash
cd ChannelMirror
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# заполни TELEGRAM_BOT_TOKEN, ADMIN_TELEGRAM_IDS, TELEGRAM_API_ID, TELEGRAM_API_HASH
python scripts/telethon_login.py --qr   # QR login → TELEGRAM_SESSION
# или phone-код: python scripts/telethon_login.py  (код чаще в чате Telegram, не SMS)
uvicorn app.main:app --host 0.0.0.0 --port 8003
```

## Команды бота

`/dests` `/sources` `/routes` `/del_route` `/toggle_route` `/interval ID SEC`

## Стек

FastAPI + aiogram + Telethon + SQLite (как SmartDigest / TravelDeals).
