# bots-python — статус (Growth OS)

Канон: `docs/VISION.md`. План: `docs/business-plan.md`. Согласовано: `docs/agreed.md`.

## В работе
- [ ] AiGateway: согласовать план (`AiGateway/PLAN.md`), потом MVP. → commit: `docs(aigateway): plan gateway service`

## Очередь
- [ ] #10 живой прогон: token + marker + канал. → commit: —
- [ ] #8 SmartDigest: ИИ-выжимка в бот (главный гэп). → commit: `feat(smartdigest): ai digest to bot`
- [ ] #8 позже: SQLite → PostgreSQL. → commit: `feat(smartdigest): migrate to postgresql`
- [ ] #3 AI-автомат (user-facing). Инфра = `AiGateway/`, не путать. → commit: `feat(ai): …`
- [ ] #7 Кино-бот без Reels. → commit: `feat(cinema): …`
- [ ] #9 Гороскопы. → commit: `feat(horoscope): …`
- [ ] #7 Reels — на потом. → commit: позже

## Сделано
### 2026-09-29
- **api-cloud: ГИБДД недоступен.** Support: «ГИБДД не работает, остальное ок». Этап 1 → гибрид (облако + ru-api на ГИБДД). → commit: `docs(api-cloud): gibdd unavailable hybrid plan`
### 2026-09-28
- **#52 этап 1 = автовладелец.** `scenarios.md`: P0 fines/preview/report; этап 2+ отложен. Ideals #52 → api-cloud. → commit: `docs(api-cloud): stage1 auto-owner scenarios`
- **Заявка ФЛ api-cloud.** Черновик письма `api-cloud.ru/reg-request-fl.md` (support + API этапа 1). → commit: `docs(api-cloud): fl registration email draft`
- **api-cloud.ru каталог.** Папка `api-cloud.ru/`: CATALOG.md + catalog.json (~33 API, ~80 методов с ценами) + черновик scenarios.md. → commit: `docs(api-cloud): catalog methods and prices`
- **#46 API-разбор.** WB/Ozon: остатки+отзывы ок; поиск WB=Jam; конкуренты WB нет в Seller; Ozon отзывы≈Premium Plus; Performance ≠ Seller. Матрица в `docs/ideals.md`. → commit: `docs(ideals): seller-assistant api matrix`
- **Ideals слиты.** Корневой черновик → `docs/ideals.md` волна 3 (#46–52) + скоринг; корень = указатель. → commit: `docs(ideals): sync wave 3 and scores`
- **Карта antru.** `docs/antru-map.md` + правило `.cursor/rules/antru-vps-map.mdc` (обновлять при деплое/доменах). → commit: `docs(antru): server map and agent rule`
### 2026-09-25
- **Док деплоя.** `docs/deploy.md` — шаблон выката ботов на antru по образцу ChannelMirror. → commit: `docs(deploy): vps bot deploy guide`
- **GHA автодеплой.** Secrets `SSH_*` + path-filter workflow; rerun success. → commit: `ci(channelmirror): fix scp exclude syntax`
- **ChannelMirror на antru.** `/opt/bots/channelmirror`, compose up, Telethon + polling ок; локальный процесс остановлен. → commit: `chore(channelmirror): docker compose and vps deploy`
- **План AiGateway.** Отдельный сервис filter/rewrite над OpenRouter free для всех ботов. → commit: `docs(aigateway): plan gateway service`
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
