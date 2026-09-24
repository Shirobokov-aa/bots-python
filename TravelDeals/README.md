# TravelDeals

Telegram-бот + канал горящих авиа/отелей/комбо-туров. CPA через Travelpayouts (Aviasales + Hotellook).

Идея #10 в `../agreed.md`. Статус: [`STATUS.md`](STATUS.md).

## Что умеет

- `/flight` — поиск билетов
- `/hotel` — поиск отелей
- `/tour` — комбо авиа + отель
- `/alert` / `/alerts` — ценовые алерты в ЛС
- Фон: раз в `DEAL_TICK_SECONDS` постит в канал **фото + текст + ссылка**
- Админ `/post_now` — сразу прогнать воркер

«Тур» в MVP = билет + отель на близкие даты (не Level.Travel).

## Setup

1. Бот у [@BotFather](https://t.me/BotFather) → `TELEGRAM_BOT_TOKEN`
2. Канал: создай, добавь бота **админом** с правом постить → `TELEGRAM_CHANNEL_ID` (например `-100…`)
3. [Travelpayouts](https://www.travelpayouts.com/) → Aviasales + Hotellook → `TRAVELPAYOUTS_TOKEN` и `TRAVELPAYOUTS_MARKER`
4. Опционально `CHANNEL_LINK=https://t.me/your_channel` для /start
5. `ADMIN_TELEGRAM_IDS` — твой telegram id для `/post_now`

```bash
cd bots-python/TravelDeals
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# заполни .env
uvicorn app.main:app --host 0.0.0.0 --port 8002
```

`GET /health` — живость. Порт **8002** (SmartDigest на 8001).

## Docker

```bash
docker compose up --build
```

## Направления воркера

Правь [`routes.yaml`](routes.yaml): origins, destinations, пороги цен.

## Тесты

```bash
pytest
```
