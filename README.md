# bots-python — monorepo TG-ботов

Один репозиторий = портфель продуктов (Growth OS). Каждый бот — **отдельный сервис** в своей папке, общий канон в `docs/`.

## Структура

```
bots-python/
  docs/                 канон мышления и план
  ChannelMirror/        #11 silent copy источников → свои каналы
  TravelDeals/          #10 авиа/отели/туры + CPA канал
  SmartDigest/          #8 дайджест из открытых каналов
  STATUS.md             кросс-статус портфеля
  CLAUDE.md             правила агента (STATUS + коммиты)
```

## Документы

| Файл | Зачем |
|------|--------|
| [`docs/VISION.md`](docs/VISION.md) | Канон смысла |
| [`docs/agreed.md`](docs/agreed.md) | Что согласовали строить |
| [`docs/business-plan.md`](docs/business-plan.md) | Живой план работ |
| [`docs/ideals.md`](docs/ideals.md) | Банк сырых идей |
| [`docs/product-marketing.md`](docs/product-marketing.md) | Маркетинг-контекст |
| [`STATUS.md`](STATUS.md) | Что в работе / очередь / сделано |

Статус конкретного бота: `<Bot>/STATUS.md`.

## Боты

| Папка | # | Суть | Порт (dev) |
|-------|---|------|------------|
| [`ChannelMirror/`](ChannelMirror/) | 11 | источники → свои каналы, silent copy | 8003 |
| [`TravelDeals/`](TravelDeals/) | 10 | поиск + алерты + канал CPA | 8002 |
| [`SmartDigest/`](SmartDigest/) | 8 | каналы → ИИ-выжимка в бот | 8001 |

Запуск — из папки бота (`README.md` внутри). Секреты только в `<Bot>/.env` (не коммитить).

## Git

Один remote на весь monorepo. Старый отдельный репо SmartDigest (`Shirobokov-aa/SmartDigest`) — архив; код живёт здесь.

## Стек (общий паттерн)

FastAPI · aiogram · SQLite (потом PostgreSQL) · Docker per bot
