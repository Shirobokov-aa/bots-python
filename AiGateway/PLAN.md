# AiGateway — план / идея / модель

**Статус:** только план (код ещё нет)  
**Дата:** 2026-09-25  
**Связь:** #3 AI в портфеле Growth OS; первый потребитель — ChannelMirror (`# TODO(ai)`), потом SmartDigest и другие боты.

---

## 1. Идея (одна фраза)

Отдельный HTTP-сервис **«мозг для ботов»**: любой продукт из `bots-python/` шлёт текст (и позже медиа-метаданные) → получает **решение** (оставить/выбросить) и/или **новый текст**. Ключи LLM и лимиты живут здесь, не в каждом боте.

Это не Telegram-бот и не Claude Code. Это тонкий **API-шлюз** над провайдерами (сначала OpenRouter free).

---

## 2. Зачем отдельно

| Без шлюза | Со шлюзом |
|-----------|-----------|
| Ключ OpenRouter в каждом `.env` | Один ключ, один лимит 50 req/день |
| Смена модели = правки во всех ботах | Меняешь `MODEL_*` в одном месте |
| Разная логика filter/rewrite | Один контракт `/v1/*` |
| Сложно шарить между ChannelMirror / SmartDigest / чатами | Подкинул `AI_BASE_URL` + `AI_API_KEY` |

Паттерн как у остальных: папка-сервис в monorepo `bots-python/AiGateway/`.

---

## 3. Границы (что делает / не делает)

**Делает**
- Filter: «публиковать пост?» → yes/no + reason  
- Rewrite: «перепиши текст под стиль / без рекламы источника» → новый text  
- (позже) Digest: несколько текстов → одна выжимка (SmartDigest)  
- Auth по `X-Api-Key`, простой rate-limit, логирование usage  

**Не делает**
- Не читает Telegram сам  
- Не постит в каналы  
- Не хранит длинную историю диалогов (MVP — stateless request/response)  
- Не обходит ToS через Claude Code CLI  

---

## 4. Модель продукта (домены)

### Клиенты
Любой внутренний сервис: ChannelMirror, SmartDigest, будущие боты/чаты.

### Операции (MVP)

| Операция | Вход | Выход | Зачем |
|----------|------|-------|-------|
| `filter` | text, optional meta (source, lang) | `{ allow: bool, reason: str }` | Отсев рекламы/мусора до очереди |
| `rewrite` | text, optional style / rules | `{ text: str }` | Silent-copy «своим» голосом |

### Операции (фаза 2)
| Операция | Зачем |
|----------|-------|
| `digest` | SmartDigest: N постов → 1 выжимка |
| `classify` | теги/тема для роутинга |
| `vision` | опционально подпись по картинке (дорого по лимитам free) |

### Провайдер (MVP)
- **OpenRouter**, OpenAI-compatible  
- Модель по умолчанию: `openrouter/free` (роутер free)  
- Опционально зафиксировать: filter → `nvidia/nemotron-3.5-content-safety:free` или gemma; rewrite → `google/gemma-4-26b-a4b-it:free` / `qwen/qwen3.8-27b:free`  
- Без paid fallback (баланс $0 → только `:free`)  

### Лимиты (важно для модели)
- ~**50 free req/сутки** на аккаунт OpenRouter без покупки кредитов  
- ChannelMirror: filter+rewrite = **2 req на пост** → ~25 постов/день на free  
- В шлюзе: дневной счётчик, при исчерпании — `429` или fail-open/fail-closed (настройка)  

---

## 5. API-контракт (черновик)

База: `http://127.0.0.1:8010` (локально) / позже URL на VPS.

```
POST /v1/filter
Header: X-Api-Key: <shared secret>
Body: {
  "text": "...",
  "meta": { "source": "theyseeku", "bot": "channelmirror" }  // optional
}
→ 200 { "allow": true, "reason": "ok", "model": "..." }
→ 200 { "allow": false, "reason": "promo / subscribe CTA", "model": "..." }

POST /v1/rewrite
Body: {
  "text": "...",
  "instructions": "optional override",
  "meta": { "bot": "channelmirror" }
}
→ 200 { "text": "...", "model": "..." }

GET /health
→ 200 { "ok": true }
```

Ошибки: `401` нет ключа, `429` лимит, `502` провайдер лёг — клиент решает retry / пропуск AI.

---

## 6. Архитектура

```
┌─────────────┐     ┌──────────────────┐     ┌──────────────┐
│ ChannelMirror│────►│   AiGateway      │────►│ OpenRouter   │
│ SmartDigest  │ HTTP│  FastAPI         │     │ :free models │
│ другие боты  │◄────│  /v1/filter|…    │◄────│              │
└─────────────┘     └──────────────────┘     └──────────────┘
                           │
                           ▼
                    usage log (sqlite)
```

**Стек (как соседние боты):** FastAPI + pydantic-settings + httpx + SQLite (usage)  
**Без** aiogram/Telethon в этом приложении.

**Промпты:** файлы `prompts/filter.md`, `prompts/rewrite.md` — правка без релиза логики.

**Fail policy (конфиг):**
- `AI_FAIL_MODE=open` — при ошибке LLM пропустить пост как есть (MVP зеркала)  
- `AI_FAIL_MODE=closed` — при ошибке не публиковать  

---

## 7. Интеграция с ChannelMirror (после MVP шлюза)

В `ChannelMirror/app/services/ai.py` вместо stub:

1. `should_publish` → `POST /v1/filter`  
2. `transform_payload` → `POST /v1/rewrite` (только text/caption)  
3. `.env`: `AI_BASE_URL`, `AI_API_KEY`, `AI_ENABLED=true`  

Медиа без vision на MVP: фильтр/рерайт только по тексту; пустой текст + фото → allow без rewrite (или короткое «media-only»).

---

## 8. Структура репо (когда начнём код)

```
bots-python/AiGateway/
  PLAN.md          ← этот файл
  STATUS.md
  README.md
  .env.example
  requirements.txt
  app/
    main.py        # FastAPI
    config.py
    auth.py
    providers/
      openrouter.py
    routes/
      v1.py
    prompts/
      filter.md
      rewrite.md
    usage.py       # sqlite счётчик
  tests/
```

Имя папки: **`AiGateway`** (явное; не путать с продуктом-ботом #3 «AI-автомат» для юзеров — это инфра).

---

## 9. План работ (фазы)

### Фаза 0 — план (сейчас)
- [x] Идея, границы, контракт, лимиты  
- [ ] Согласовать имя/порт/fail-mode с тобой  

### Фаза 1 — MVP шлюза → `feat(aigateway): mvp filter rewrite openrouter`
- [ ] Скелет FastAPI + auth + health  
- [ ] OpenRouter client (`openrouter/free` или раздельные MODEL_FILTER / MODEL_REWRITE)  
- [ ] `/v1/filter`, `/v1/rewrite` + промпты  
- [ ] Usage sqlite + 429 при дневном лимите  
- [ ] README + `.env.example`  

### Фаза 2 — ChannelMirror → `feat(channelmirror): wire aigateway`
- [ ] Реальные вызовы в `ai.py`  
- [ ] Флаги per-route позже (опционально)  

### Фаза 3 — SmartDigest / общее
- [ ] `/v1/digest`  
- [ ] Общий клиент-хелпер `bots-python/shared/` или маленький sdk-модуль (по желанию)  

### Фаза 4 — деплой
- [ ] Docker / systemd на VPS (antru или ant-vps)  
- [ ] Доступ только Tailscale/VPN или localhost+SSH tunnel  

---

## 10. Риски и решения

| Риск | Решение |
|------|---------|
| 50 req/день мало | Сначала только filter; rewrite по флагу; или копить $10 кредитов ради 1000/день free |
| Free модель тупит | Разные MODEL_* ; A/B в логах |
| Утечка ключа шлюза | Длинный `AI_API_KEY`, не светить в git, bind 127.0.0.1 |
| Провайдер down | fail-open для зеркала |
| Путаница с #3 AI-ботом | AiGateway = инфра; #3 = отдельный user-facing продукт позже |

---

## 11. Решения, которые ждут твоего «ок»

1. Имя папки: `AiGateway` — ок?  
2. MVP: сразу filter+rewrite или сначала только filter?  
3. Default fail: **open** (пост уйдёт без AI при сбое) или closed?  
4. Где крутить сначала: localhost рядом с ChannelMirror?  

После согласования — фаза 1 код.
