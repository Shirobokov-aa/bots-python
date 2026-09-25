# ChannelMirror — статус

## В работе

## Очередь
- [ ] GHA secrets + push → автодеплой path-filter. → commit: `chore(channelmirror): docker compose and vps deploy`
- [ ] TODO(ai): фильтр рекламы/мусора перед очередью. → commit: `feat(channelmirror): ai filter`
- [ ] TODO(ai): рерайт текста. → commit: `feat(channelmirror): ai rewrite`
- [ ] Режим forward с атрибуцией (опция). → commit: `feat(channelmirror): forward mode`

## Сделано
### 2026-09-25
- **На antru.** `/opt/bots/channelmirror`, Docker, `.env`+sqlite с Mac; Telethon join + polling `@shiro_test_bot`. → commit: `chore(channelmirror): docker compose and vps deploy`
- **Fix gif + watchlist commit.** Telethon `.gif` вместо `.animation`; commit до `refresh_watchlist` (приватный Rose Signal не попадал). → commit: `fix(channelmirror): gif serialize and watchlist commit`
- **Приватные источники.** Кнопка «Приватный источник»: forward или `t.me/+` инвайт; матч по chat_id. → commit: `feat(channelmirror): private sources`
- **Живой прогон ок.** Пост из Finder.work / источников дошёл в тестовый канал. → commit: —
### 2026-09-24
- **Слушатель: join + chat_id.** Без подписки события не приходят; каналы без `@` (Finder.work) матч по peer id. → commit: `fix(channelmirror): join sources by chat id`
- **Interval 0.** `/interval ID 0` = без паузы; min 60 снят. → commit: `fix(channelmirror): allow zero interval`
- **QR рисуется в терминале + PNG.** Не открывать `tg://` на телефоне — сканить экраном. → commit: `fix(channelmirror): render telethon qr`
- **QR Telethon login.** `scripts/telethon_login.py --qr` когда SMS/код не приходит. → commit: `fix(channelmirror): qr telethon login`
- **MVP код.** Silent copy, маршруты, Telethon, очередь, `# TODO(ai)`. → commit: `feat(channelmirror): mvp silent copy queue`
- **Лок продукта #11.** → commit: `docs(agreed): lock channelmirror`
