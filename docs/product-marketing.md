# Product Marketing Context

**Document version:** v4  
**Last updated:** 2026-09-21

> Канон мышления: [`VISION.md`](VISION.md). Этот файл — сжатый контекст для marketing skills. При конфликте побеждает VISION.

## Product Overview
**One-liner:** Кинул в бота открытые TG-каналы — получаешь одно красивое ИИ-сообщение-выжимку (RU); дальше такие автоматы размножаем по разным нишам без ежедневных рук.

**What it does (первый продукт — SmartDigest):** Пользователь добавляет ссылки/@ на открытые каналы. Бот читает посты, ИИ сжимает важное в одну аккуратную выжимку, отдаёт **в бот** (автопост в канал — позже). Вокруг — фон + позже дашборд (Next.js) и другие ниши из ideals на том же паттерне (FastAPI + PostgreSQL). Ниши могут быть из разных направлений.

**Product category:** Autonomous media OS / growth automation platform

**Product type:** Internal platform first → later optional SaaS/white-label for media operators

**Business model:**
- Сейчас: CPA + реклама в собственных поверхностях (каналы/боты), VIP в ботах
- Потом: OS как продукт (подписка / white-label шаблоны ниш)

**Stack (минимум):** FastAPI (Python) · Next.js · PostgreSQL · Telegram Bot API

## Target Audience

### A. Конечная аудитория поверхностей (B2C)
**Кто:** Telegram-users, **RU only** на старте; хотят сжатый полезный поток без серфа  
**Primary use case:** Получать ценность на автопилоте  
**Jobs to be done:**
- Не читать десятки источников
- Не пропустить релевантное в нише
- Быстрый action (ссылка, бот, сохранение)

### B. Оператор / будущий клиент OS
**Кто:** Сейчас — solo-основатель. Потом — медиа-операторы, арбитраж, мелкие сетки  
**Primary use case:** Запустить и забыть контур роста  
**Jobs to be done:**
- Один раз сконфигурировать нишу
- Смотреть метрики, убивать лузеров
- Клонировать победителей без нового кода

## Personas
| Persona | Cares about | Challenge | Value we promise |
|---------|-------------|-----------|------------------|
| Подписчик | Польза, частота, мало шума | Лента токсична и длинна | Автопоток под нишу |
| Юзер бота | Стабильный инструмент | Ручной труд вокруг инфо | Бот как крючок и utility |
| Оператор | Автономия, юнит-экономика | Руки на контенте = потолок | OS крутит фон |
| (later) Клиент SaaS | Time-to-niche, надёжность | Собрать пайплайн с нуля | Шаблон ниши + дашборд |

## Problems & Pain Points
**Core problem:** Рост в TG требует ежедневных рук; руки не масштабируются.

**Why alternatives fall short:**
- SMM-планировщики — не думают и не парсят
- Один канал вручную — потолок времени основателя
- Отдельные боты без мозга — нет общей оптимизации
- Агентства — дорого, зависимость от людей

**What it costs them:** Время основателя, упущенный CPA, нестабильный график постов  
**Emotional tension:** «Либо живу, либо веду каналы»

## Competitive Landscape
**Direct:** Автопостинг + LLM-рерайт тулы — обычно без ingest+learn+clone как OS  
**Secondary:** Ручные медиасетки — люди в центре  
**Indirect:** RSS-reader / Saved Messages — нет дистрибуции и денег

## Differentiation
**Key differentiators:**
- Цель = автономность (месяц без ноута), не «помочь постить»
- Слои: Ingest → Transform → Distro → Acquire → Monetize → Learn → Clone
- Control plane (Next.js) + один PostgreSQL-мозг
- SmartDigest как задел ingest; PriceWatcher снят с доски

**How we do it differently:** Конфиг ниши > новый код. Метрики кормят следующий цикл.  
**Why that's better:** Масштаб поверхностей без масштаба часов.  
**Why customers choose us:** (пока) оператор выбирает свободу от рутины.

## Objections
| Objection | Response |
|-----------|----------|
| «Автоконтент = шлак» | Политики тона + QA на старте + Learn режет слабые форматы |
| «Бан канала / антиспам» | Диверсификация поверхностей, slow growth, kill-switch |
| «Слишком амбициозно» | Phase 0–1: один замкнутый контур прежде SaaS |

**Anti-persona:** Кто хочет личный блог с лицом и ежедневным творчеством.  
Кто ищет «кнопку деньги» без настройки политик и офферов.

## Switching Dynamics
**Push:** Выгорание от ручного постинга  
**Pull:** Система живёт в фоне, дашборд раз в неделю  
**Habit:** «Сегодня вечером что-нибудь напишу»  
**Anxiety:** LLM-бред, бан, пустые метрики месяцами

## Customer Language
**How they describe the problem:**
- «нет времени вести канал»
- «хочу чтобы само росло»
- «настроил и забыл»
**How they describe us:**
- «автопилот для телеги»
- «фабрика каналов»
- «боты сами крутят аудиторию»
**Words to use:** автономия, контур, ниша, пайплайн, control plane, clone, юнит-экономика  
**Words to avoid:** пассивный доход без усилий, гарантия заработка, халява 100%  
**Glossary:**
| Term | Meaning |
|------|---------|
| Growth OS | Вся система автономного роста |
| Контур | Замкнутый цикл одной ниши end-to-end |
| Control plane | Next.js дашборд |
| Clone | Новая ниша копированием конфига |
| SmartDigest | Текущий задел бота-дайджеста |

## Brand Voice
**Tone:** Спокойный, системный, без инфоцыганства  
**Style:** Коротко, структурно, про петли и метрики  
**Personality:** автономный, инженерный, честный про фазы

## Proof Points
**Metrics:** SmartDigest в репо; полный OS — впереди  
**Customers:** —  
**Testimonials:** —  
**Value themes:**
| Theme | Proof |
|-------|-------|
| Автономия как цель | VISION §4 критерий «месяц без ноута» |
| Есть задел ingest | SmartDigest |
| Мёртвое отрезано | PriceWatcher удалён |

## Goals
**Business goal:** Живущий без ежедневных рук Growth OS; сначала для себя, опционально productize.  
**Conversion action (аудитория):** Подписка / старт бота / CPA-клик  
**Conversion action (оператор):** Новый контур из шаблона без кода  
**Current metrics:** 1 живой задел (SmartDigest); ниши не выбраны; PostgreSQL + Next.js — todo

## Portfolio
Ниши **не зафиксированы**. Банк идей: `ideals.md`. Правило отбора и фазы: `VISION.md` §8–9.

## Architecture (целевой)
```
Sources → FastAPI workers → PostgreSQL ← Next.js control plane
                ↓
     Telegram channels + bots (поверхности)
                ↓
           Learn loop (метрики → веса)
```

## Changelog
*Newest first.*
- v4 (2026-09-21) — Delivery = бот only; RU only; ниши разношёрстные ок.
- v3 (2026-09-21) — SmartDigest UX: открытые каналы → одна ИИ-выжимка; путь ideals→анализ→реализация.
- v2 (2026-09-21) — Рефрейм под Autonomous Growth OS; убран PriceWatcher; ссылка на VISION.md.
- v1 (2026-09-21) — Initial context from bissnes-plan + ideals + два бота.
