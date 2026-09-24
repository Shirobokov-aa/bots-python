# Архитектура

SmartDigest — один процесс: FastAPI поднимает Telegram-бот и фоновый планировщик.

```
Telegram
   │  polling (локально) или POST /telegram/webhook
   ▼
aiogram handlers  ──► SQLite (users, sources, items)
   │
   ▼
fetch
   ├─ rss       → feedparser
   ├─ telegram  → публичная страница t.me/s/<channel>
   └─ website   → поиск RSS/Atom, затем feedparser
   │
   ▼
дайджест: дедуп + эвристика рекламы → одно HTML-сообщение
```

ИИ пока нет: выжимка — список заголовков со сниппетами и ссылками. Саммари и антикликбейт — следующий этап.

## Процессы внутри `uvicorn`

При старте (`app/main.py`, lifespan):

1. Создаёт таблицы SQLite (`data/smartdigest.db`).
2. Запускает `scheduler_loop` — каждые `COLLECT_TICK_SECONDS` (60 с) опрашивает ленты и в нужный час шлёт дневной дайджест.
3. Telegram: `TELEGRAM_MODE=polling` (по умолчанию) или webhook.

Локально **не** использовать `--reload`: WatchFiles убивает polling. Запуск:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8001
```

HTTP:

- `GET /health` — жив ли процесс
- `POST /telegram/webhook` — только при `TELEGRAM_MODE=webhook`

## Модель данных

- **User** — `telegram_id`, `is_vip`, час дайджеста (`digest_hour` в `DIGEST_TIMEZONE`)
- **Source** — RSS / Telegram / сайт, интервал опроса, `is_active`
- **Item** — пост ленты, `content_hash`, флаг `is_noise`

## Лимиты

| | Бесплатно | VIP (`/grant_vip`) |
|---|---|---|
| Источников | `FREE_MAX_SOURCES` (5) | `VIP_MAX_SOURCES` (40) |
| Материалов в дайджесте | `FREE_DIGEST_ITEMS` (12) | `VIP_DIGEST_ITEMS` (30) |
| Опрос ленты | `FREE_INTERVAL_SECONDS` (3600) | `VIP_INTERVAL_SECONDS` (900) |

Приватные Telegram-каналы бот не читает: нужен публичный `@username` или RSS.
