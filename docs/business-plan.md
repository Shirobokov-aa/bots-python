# Бизнес-план (живой)

Постоянно правим. Смысл — `VISION.md`. Что строим — `agreed.md`. Сырые идеи — `ideals.md`.  
Все канон-доки живут в `docs/` (этот файл раньше назывался `bissnes-plan.md`).

**Обновлено:** 2026-09-24

---

## Цель

Портфель TG-продуктов (боты / каналы / чаты): **масштабировать и зарабатывать**. Ниши могут быть разными.  
«Настроил → крутится с малым числом рук» — желаемый контур, не единственный смысл. RU.  
Канон: `VISION.md` v3.2.

---

## Согласовано к реализации

См. `agreed.md`: **#11 ChannelMirror (в работе)**, #10 TravelDeals (код есть), #8, #3, #7 (бот без Reels), #9.  
Reels для кино — «на потом». Level.Travel для #10 — после MVP.

---

## Сейчас в фокусе

**#11 ChannelMirror** — MVP: ссылки на источники → silent copy в свои каналы (без атрибуции), очередь 1–2 ч, без ИИ (`# TODO(ai)`).

Каталог: `bots-python/ChannelMirror/`.

**#10 TravelDeals** — код MVP готов, ждём креды для живого прогона (`TravelDeals/`).

### #10 TravelDeals — есть / нет

| Есть | Нет / недоделано |
|------|------------------|
| FastAPI + aiogram + SQLite | Живой прогон (нужны token/marker/канал) |
| `/flight` `/hotel` `/tour` | Level.Travel |
| `/alert` `/alerts` + пуш в ЛС | PostgreSQL |
| Воркер → канал фото+текст+CPA | |
| Travelpayouts client + deeplink marker | |
| Docker, polling, pytest | |

#11 ChannelMirror — MVP код в `ChannelMirror/` (silent copy, очередь, TODO(ai)).  
#8 SmartDigest — задел есть, ИИ-выжимка в очереди.  
#3 / #7 / #9 — только в agreed, кода нет.

---

## Стек

FastAPI (Python) · PostgreSQL (позже; сейчас SQLite в ботах) · Next.js (дашборд позже) · Telegram Bot API · Travelpayouts CPA

---

## Этапы

| Этап | Что | Статус |
|------|-----|--------|
| A | Лок идей в `agreed.md` | **сделано** (+ #10) |
| B0 | **#10 TravelDeals MVP** | **код готов**, ждём креды |
| B0b | #11 ChannelMirror MVP (silent copy) | **в работе** |
| B | #8 SmartDigest: каналы → ИИ → сообщение в бот | очередь |
| C | #3 AI-автомат | очередь |
| D | #7 Кино-бот без Reels | очередь |
| E | #9 Гороскопы-бот | очередь |
| F | Куда постить выжимку SmartDigest (канал) | отложено |
| G | #7 Reels-трафик | на потом |
| H | Дашборд Next.js + метрики | позже |
| I | CPA / реклама / рост | частично через #10 |

---

## Решения

- #10: поиск + пуши + канал; «тур» = авиа+отель; RU; Travelpayouts marker
- Язык **RU**
- Ниши могут быть разными
- PriceWatcher — мёртв
- Согласованное из `agreed.md` **не убираем**

---

## Открыто

- Нужны `TRAVELPAYOUTS_TOKEN` + `TRAVELPAYOUTS_MARKER` + канал + bot token

---

## Changelog
- 2026-09-24 — Monorepo: файл → `docs/business-plan.md` (бывш. `bissnes-plan.md`). Фокус → #11 ChannelMirror MVP.
- 2026-09-23 — Лок #11 ChannelMirror.
- 2026-09-22 — Фокус → #10 TravelDeals MVP.
- 2026-09-21 — Снимок «есть/нет» по SmartDigest; фокус = этап B.
- 2026-09-21 — Лок четырёх идей; этап A закрыт; Reels кино → G на потом.
- 2026-09-21 — Живой план вместо устаревшего скелета.
