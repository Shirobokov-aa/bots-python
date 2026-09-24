# Запуск

Нужен Python 3.11+ (на Маке команда `python3`).

## 1. Окружение

```bash
cd bots-python/SmartDigest
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## 2. `.env`

Обязательно:

| Ключ | Что |
|---|---|
| `TELEGRAM_BOT_TOKEN` | токен от [@BotFather](https://t.me/BotFather) |
| `ADMIN_TELEGRAM_IDS` | твой числовой Telegram ID ([@userinfobot](https://t.me/userinfobot)) |

Локально `TELEGRAM_MODE=polling`. Часовой пояс дайджеста: `DIGEST_TIMEZONE=Europe/Moscow`, час по умолчанию `DEFAULT_DIGEST_HOUR=9`.

Файл `.env` в git не попадает. После правки перезапусти процесс.

## 3. Старт

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

В логе:

```
scheduler started tick=60s
polling on
Application startup complete.
```

`--reload` не использовать.

## 4. Docker

```bash
docker compose up --build
```

Порт 8001 по умолчанию.

## Тесты

```bash
python -m pytest -q
```
