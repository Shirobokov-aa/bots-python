# Деплой ботов на VPS (antru)

Как выкатывать сервисы из monorepo `bots-python` на Beget VPS.  
Эталон в проде: **ChannelMirror** → `/opt/bots/channelmirror` + workflow `.github/workflows/deploy-channelmirror.yml`.

Нюансы у каждого бота свои (БД, webhook, Telethon-session) — ниже каркас, не догма.

---

## Картина

| | |
|---|---|
| Сервер | SSH host `antru-vps` (`155.212.146.175`, Beget) |
| Proxy | Caddy в `/opt/apps/caddy` (сеть Docker `proxy`) |
| Боты | обычно `/opt/bots/<имя>` |
| Сайты | `/opt/apps/<имя>` (другой паттерн, см. `shir0.com`) |
| Repo | `Shirobokov-aa/bots-python`, ветка `main` |
| Секреты GHA | `SSH_HOST`, `SSH_USER`, `SSH_PRIVATE_KEY` (уже в репо; тот же ключ, что у portfolio) |

```
push main (paths: BotName/**)
  → GitHub Actions
    → SCP кода на VPS (без .env / data)
    → docker compose up -d --build
```

**Один бот = одна папка = свой compose = свой path-filter workflow.**  
Коммит в чужую папку чужой сервис не трогает.

Другой VPS (`ant-vps` / Hetzner) — VPN/Claude Code, **не** хостинг ботов по умолчанию.

---

## Правила (держимся)

1. **Сервис изолирован** — код, `.env`, volumes только внутри своей папки на сервере.
2. **`.env` и `data/` не в git** и не синкать деплоем (`rm: false` + файлов нет в checkout).
3. **Path-filter** в workflow — деплой только при изменении этой папки (или самого yaml).
4. **Один polling-токен = один процесс.** Локальный uvicorn с тем же `TELEGRAM_BOT_TOKEN` перед продом остановить.
5. **Тома БД не пересоздавать** — у Postgres `external: true` + стабильное имя volume (как у сайтов на antru).
6. **Публичный HTTP** (webhook) — только через Caddy + сеть `proxy`. Polling-боту домен не нужен.

---

## Чеклист: новый бот на прод

Подставь `BotName` / `botname` (папка vs путь на диске).

### 1. В репо (папка бота)

- [ ] `Dockerfile` + `docker-compose.yml` (сервис `bot`, `env_file: .env`, volume `./data` если SQLite)
- [ ] `.dockerignore` (`.venv`, `data`, `.env`, тесты, STATUS…)
- [ ] `.env.example` полный; секреты только локально / на сервере
- [ ] `STATUS.md` — задача деплоя

Минимум compose (polling, SQLite):

```yaml
services:
  bot:
    build: .
    container_name: botname
    env_file: .env
    volumes:
      - ./data:/app/data
    restart: unless-stopped
    expose:
      - "800X"
```

С Postgres — добавь сервис `db`, named volume с `external: true` после первого создания, миграции отдельным шагом в script деплоя.

### 2. Workflow

Файл: `.github/workflows/deploy-<botname>.yml`  
Скопируй `deploy-channelmirror.yml`, замени:

| Поле | Пример |
|------|--------|
| `paths` | `BotName/**`, путь к yaml |
| `concurrency.group` | `deploy-botname` |
| `source` / `target` | `BotName/` → `/opt/bots/botname` |
| `strip_components` | `1` |
| script `cd` | `/opt/bots/botname` |

Exclude через `!` в `source` (отдельного `exclude:` у scp-action нет):

```yaml
source: "BotName/,!BotName/.venv,!BotName/data,!BotName/tests,!BotName/STATUS.md,!BotName/README.md"
```

Секреты `SSH_*` уже есть — новые не плодить, пока тот же сервер.

### 3. Первый заливка (bootstrap, один раз)

Локально бот с этим токеном **не** должен крутиться.

```bash
# каталог + код (или rsync своей папки)
ssh antru-vps 'mkdir -p /opt/bots/botname/data'

rsync -az --exclude '.venv' --exclude '__pycache__' --exclude '.pytest_cache' \
  BotName/ antru-vps:/opt/bots/botname/

# .env и при необходимости существующую sqlite/data — руками / scp один раз
scp BotName/.env antru-vps:/opt/bots/botname/.env

ssh antru-vps 'cd /opt/bots/botname && docker compose up -d --build'
ssh antru-vps 'docker logs -f botname'   # container_name из compose
```

Потом: commit workflow + compose → push `main` → проверить Actions → дальше только git.

### 4. Если нужен HTTPS / webhook

1. Compose: сеть `proxy` (external) + `expose` порта приложения (без publish на хост).
2. Блок в `/opt/apps/caddy/conf/Caddyfile`.
3. `docker exec caddy caddy reload --config /etc/caddy/Caddyfile`
4. DNS A/AAAA на `155.212.146.175`
5. В `.env` на сервере: `TELEGRAM_MODE=webhook`, URL, secret.

Polling — этот шаг пропускаешь.

### 5. Обновления

Обычный цикл: правки в `BotName/` → commit → push `main` → GHA.

Вручную:

```bash
ssh antru-vps 'cd /opt/bots/botname && docker compose up -d --build'
ssh antru-vps 'docker compose -f /opt/bots/botname/docker-compose.yml logs -f --tail=100'
```

Смена секретов: правь **только** `/opt/bots/botname/.env` на VPS, потом `docker compose up -d` (или recreate). В git не коммить.

---

## Что не синкать деплоем

| Путь | Почему |
|------|--------|
| `.env`, `.env.*` | секреты |
| `data/`, `*.db`, media | состояние |
| `*.session`, Telethon session в env | аккаунт |
| `.venv`, тесты, STATUS/README | мусор / не рантайм |

`rm: false` в scp — не удалять на сервере файлы, которых нет в артефакте (как раз `.env` / `data`).

---

## Нюансы по типам сервисов

| Тип | Что учесть |
|-----|------------|
| Polling-бот | Без Caddy; один инстанс на токен |
| Webhook-бот | Caddy + `proxy` + URL в BotFather/env |
| SQLite | Volume `./data`; бэкап = копия `data/` |
| Postgres | Named volume + `external: true`; миграции в deploy script |
| Telethon / user-session | `TELEGRAM_SESSION` только в `.env` на VPS; логин лучше один раз локально |
| Shared (AiGateway) | Отдельная папка + свой workflow; боты ходят по URL/ключу; ключи LLM только в шлюзе |
| Несколько ботов в одном push | Несколько path-filter job'ов; concurrency **разный** на сервис |

Общий код (`shared/`, AiGateway): либо path-filter включает потребителей, либо отдельный workflow + ручной/явный рестарт зависимых сервисов.

---

## Эталон и соседние проекты

| Что | Где |
|-----|-----|
| Живой бот | `/opt/bots/channelmirror` на antru |
| Workflow | `.github/workflows/deploy-channelmirror.yml` |
| Сайт с тем же SSH | `shir0.com` → `/opt/apps/portfolio` (SCP всего репо, другой layout) |
| Карта VPS / Caddy | репо `caddy-vs-dokploy`, docs `antru-vps_beget/07-migration-done.md` |

Проверка после деплоя:

```bash
ssh antru-vps 'docker ps --filter name=channelmirror'
ssh antru-vps 'docker logs channelmirror --tail=50'
```

---

## Антипаттерны

- Один `docker-compose` на весь monorepo с `up --build` всего портфеля на каждый коммит  
- Класть `.env` в git или в SCP-артефакт  
- `docker volume prune` / `system prune --volumes` на antru (сносит БД сайтов и ботов)  
- Два процесса с одним bot token (Mac + VPS)  
- Деплой ботов на `ant-vps` «потому что там Claude» — другая роль машины  

---

## Короткий шаблон имени

```
папка репо:     TravelDeals/
путь VPS:       /opt/bots/traveldeals
container:      traveldeals
workflow:       deploy-traveldeals.yml
concurrency:    deploy-traveldeals
```

Имена можно выровнять иначе — главное **один сервис ↔ один target ↔ один path-filter**.
