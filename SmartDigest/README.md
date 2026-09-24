SmartDigest — Telegram-бот на FastAPI. Собирает RSS, сайты и публичные каналы, присылает одну выжимку за день.

Документация: [`docs/`](docs/README.md). ИИ-саммари пока нет — фильтр повторов и рекламы эвристический.

## Запуск локально

```bash
cd bots-python/SmartDigest
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

В `.env` вставь `TELEGRAM_BOT_TOKEN` от [@BotFather](https://t.me/BotFather).

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

По умолчанию `TELEGRAM_MODE=polling`. Для продакшена:

```
TELEGRAM_MODE=webhook
TELEGRAM_WEBHOOK_URL=https://your.domain/telegram/webhook
TELEGRAM_WEBHOOK_SECRET=random-string
```

`GET /health` — жив ли сервис. `--reload` не использовать.

## Команды

- RSS, сайт или `@канал` — новый источник
- `/sources` — ленты, пауза, ручное обновление, удаление
- `/digest` — выжимка за сутки
- `/time` — час ежедневной рассылки (часовой пояс `DIGEST_TIMEZONE`)
- `/vip` — лимиты
- `/grant_vip <telegram_id>` — только `ADMIN_TELEGRAM_IDS`

Бесплатно: 5 источников, 12 материалов в дайджесте. VIP: 40 лент и 30 материалов.

## Docker

```bash
docker compose up --build
```
