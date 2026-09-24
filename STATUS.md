# bots-python — статус (Growth OS)

Канон: `docs/VISION.md`. План: `docs/business-plan.md`. Согласовано: `docs/agreed.md`.

## В работе
_(пусто)_

## Очередь
- [ ] #11 живой прогон: bot token + Telethon session + канал. → commit: —
- [ ] #10 живой прогон: token + marker + канал. → commit: —
- [ ] #8 SmartDigest: ИИ-выжимка в бот (главный гэп). → commit: `feat(smartdigest): ai digest to bot`
- [ ] #8 позже: SQLite → PostgreSQL. → commit: `feat(smartdigest): migrate to postgresql`
- [ ] #3 AI-автомат. → commit: `feat(ai): …`
- [ ] #7 Кино-бот без Reels. → commit: `feat(cinema): …`
- [ ] #9 Гороскопы. → commit: `feat(horoscope): …`
- [ ] #7 Reels — на потом. → commit: позже

## Сделано
### 2026-09-24
- **Monorepo порядок:** `docs/` (VISION/agreed/business-plan/ideals), gitignore, `git init` на `bots-python/`, убран nested `SmartDigest/.git`. → commit: `chore(repo): monorepo layout and docs`
- **#11 ChannelMirror MVP** в `ChannelMirror/`: silent copy, очередь, TODO(ai). → commit: `feat(channelmirror): mvp silent copy queue`
- **Лок #11 → в работе.** → commit: `docs(agreed): channelmirror in progress`

### 2026-09-23
- **Лок #11 ChannelMirror** — источники → свои каналы, полный репост. Не путать с #8. → commit: `docs(agreed): lock channelmirror`

### 2026-09-22
- **#10 TravelDeals MVP** в `TravelDeals/`: поиск, алерты, канал, CPA. → commit: `feat(traveldeals): mvp bot channel and deals`
- **Лок #10** → в работе. → commit: `docs(agreed): lock traveldeals in progress`
- **Короткий разбор** ideals (#1–45). → commit: `docs(ideals): short review all ideas`
- **VISION v3.2.** → commit: `docs(vision): scale and monetize over similarity`
- **Волна 2 идей** #11–45. → commit: `docs(ideals): add bot and chat ideas`

### 2026-09-21
- **Снимок прогресса** в `business-plan.md`. → commit: `docs(plan): snapshot smartdigest gaps`
- **Лок #8 #3 #7 #9**. → commit: `docs(agreed): lock four ideas`
