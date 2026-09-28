# Карта сервера antru (Beget)

**Обновляй этот файл** при любом изменении на VPS: новый сервис, домен, контейнер, путь, стоп/удаление.  
Правило агента: `.cursor/rules/antru-vps-map.mdc`.

| | |
|---|---|
| SSH host | `antru-vps` |
| IP | `155.212.146.175` |
| Proxy | Caddy 2.x → `/opt/apps/caddy/conf/Caddyfile` |
| Сеть web↔Caddy | Docker `proxy` |
| Боты (monorepo) | `/opt/bots/<имя>` |
| Сайты / стеки | `/opt/apps/<имя>` |
| Деплой ботов | [`deploy.md`](deploy.md) |

Снято с живого хоста: **2026-09-28**.

---

## Домены (Caddyfile)

Источник истины на сервере: `/opt/apps/caddy/conf/Caddyfile`.

| Домен | Upstream | Проект на диске |
|-------|----------|-----------------|
| [shir0.ru](https://shir0.ru) | `shiro-portfolio:3000` | `/opt/apps/portfolio` |
| [arty.shir0.ru](https://arty.shir0.ru) | `arty-website-51ty5v-app-1:3000` | `/opt/apps/arty` |
| [arty-v2.shir0.ru](https://arty-v2.shir0.ru) | `landsite:3000` | `/opt/apps/landsite` |
| [divitex.shir0.ru](https://divitex.shir0.ru) | `divitex-main-pjwv9l-app-1:3000` | `/opt/apps/divitex` |
| [dev-corp.shir0.ru](https://dev-corp.shir0.ru) | `shir0-mainandbot-img4pu-app-1:3000` | `/opt/apps/corp` |

**Нет в Caddy (offline / DNS отдельно):** `carwash.shir0.ru`, `s-lounge.shir0.ru`, `re-line.shir0.ru`.

Боты polling — **без** публичного домена (Telegram long-poll).

---

## Боты `/opt/bots`

| Путь VPS | Контейнер | Порт (expose) | Telegram | Репо / workflow |
|----------|-----------|---------------|----------|-----------------|
| `/opt/bots/traveldeals` | `traveldeals` | 8002 | `@bilet_na_stol_bot` · канал [@bilet_na_stol](https://t.me/bilet_na_stol) | `bots-python/TravelDeals` · `deploy-traveldeals.yml` |
| `/opt/bots/channelmirror` | `channelmirror` | 8003 | `@shiro_test_bot` | `bots-python/ChannelMirror` · `deploy-channelmirror.yml` |

`.env` и `data/` только на сервере, в git нет.

---

## Сайты / стеки `/opt/apps`

| Путь | Compose / контейнеры | Домен | БД |
|------|----------------------|-------|-----|
| `/opt/apps/caddy` | `caddy` | — (proxy) | тома сертов Caddy |
| `/opt/apps/portfolio` | `shiro-portfolio` | shir0.ru | — |
| `/opt/apps/arty` | app + `arty-telegram-bot-1` + postgres | arty.shir0.ru | named volume postgres |
| `/opt/apps/landsite` | `landsite` | arty-v2.shir0.ru | uploads volume |
| `/opt/apps/divitex` | app + postgres | divitex.shir0.ru | named volume postgres |
| `/opt/apps/corp` | app + bot + db (`shir0-mainandbot-img4pu-*`) | dev-corp.shir0.ru | named volume postgres |

Порты на хосте снаружи: только **80** / **443** (Caddy). App/bot/db — внутри Docker.

---

## Как проверить живое состояние

```bash
ssh antru-vps 'docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Image}}"'
ssh antru-vps 'cat /opt/apps/caddy/conf/Caddyfile'
ssh antru-vps 'ls /opt/bots /opt/apps'
```

После расхождения с этой таблицей — **сразу править этот файл** (дата сверху + changelog).

---

## Changelog

| Дата | Что |
|------|-----|
| 2026-09-28 | Карта создана: 5 доменов Caddy, traveldeals + channelmirror в `/opt/bots`, сайты в `/opt/apps`. |
