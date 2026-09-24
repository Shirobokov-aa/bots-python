# SmartDigest — статус

**Ветка:** `main`  
**Контур сессии:** локальный polling (`uvicorn`, без `--reload`).

## В работе

_

## Очередь

- [ ] **ИИ-саммари.** Кликбейт, реклама, повторы и стиль выжимки — после стабильного сбора лент. → commit: `feat(ai): summarize digest with llm`
- [ ] **Тематические подборки.** Готовые ленты («AI за день», «крипта») как платный продукт. → commit: `feat(catalog): curated topic digests`

## Сделано

### 2026-09-11

- **Каркас бота без ИИ.** FastAPI + aiogram + SQLite: RSS / публичный Telegram / сайт, сбор постов, эвристический дайджест по кнопке и раз в день. ИИ не подключали. → commit: `feat(smartdigest): bootstrap fastapi bot with rss digest`
