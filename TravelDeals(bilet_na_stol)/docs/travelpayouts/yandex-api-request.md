# Заявка на API Яндекс Путешествий

Источники:

- Travelpayouts HC: https://support.travelpayouts.com/hc/ru/articles/19677424987026
- Офиц. API: [Авторизация](https://yandex.ru/dev/travel-partners-api/doc/ru/authorization), [Быстрый старт](https://yandex.ru/dev/travel-partners-api/doc/ru/getting-started), [Лимиты](https://yandex.ru/dev/travel-partners-api/doc/ru/limits)
- Шпаргалка методов/curl: [yandex-travel-api.md](yandex-travel-api.md)

**Статус (2026-09-28):** написали в чат Яндекса → пришёл чеклист (не отказ).  
Порог ~5k MAU из HC Travelpayouts в ответе **не фигурировал**. Дальше — whitelist логина + OAuth. Шпаргалка API собрана.

---

## Ответ Яндекса (факт)

Требования:

1. Аккаунт Яндекса (владелец бизнеса, постоянный доступ, желательно 2FA).
2. OAuth 2.0 — токен на **1 год**, заголовок `Authorization: OAuth <token>`.
3. Лимит: **≤ 50 запросов/сек** с одного IP (`429` при превышении).

Ссылки из ответа:

- https://yandex.ru/dev/travel-partners-api/doc/ru/authorization  
- https://yandex.ru/dev/travel-partners-api/doc/ru/getting-started  
- https://yandex.ru/dev/travel-partners-api/doc/ru/limits  

По [быстрому старту](https://yandex.ru/dev/travel-partners-api/doc/ru/getting-started): партнёр → **whitelist логина** (пишут в support, ~сутки, письмо на почту Яндекс ID) → OAuth-токен → тестовый запрос.

---

## Что делать сейчас (после их ответа)

| # | Действие | Готово когда |
|---|----------|--------------|
| 1 | Выбрать **постоянный** Яндекс-аккаунт владельца + включить 2FA | Аккаунт готов |
| 2 | Ответить в тот же чат: «добавьте логин в whitelist» + указать логин | Сообщение ушло |
| 3 | Ждать ~сутки письмо на почту Яндекс ID | «Логин в whitelist» |
| 4 | Открыть OAuth (под тем же аккаунтом): | Token в URL / на экране |
|   | `https://oauth.yandex.ru/authorize?response_type=token&client_id=b0ca9cd48f66420c9995c0776f2243a8` | |
| 5 | Сохранить token в `.env` как `YANDEX_TRAVEL_OAUTH=` (**не в git**) | Переменная есть |
| 6 | Тест из docs: `GET …/hotels/hotel/?hotel_id=1019057204` + заголовок OAuth | JSON отеля, не 401/403 |
| 7 | Код бота: `hotels/search` / `top-offers` → цена в `/hotel` и канал; URL → Links API | Пост «отель от N ₽» |
| 8 | В коде не долбить API: лимит 50 rps; для бота хватит редких запросов | Без 429 |
| 9 | Через ~11–12 мес — новый токен | Напоминание |

Параллельно: авиа + hotel deeplink (P8) работают без этого токена.

---

## Черновик ответа в чат (whitelist)

```
Спасибо!

Прошу добавить в whitelist логин Яндекс ID для доступа к Travel Partners API:

Логин: [ваш_логин]
Почта Яндекс ID: [email@yandex.ru]
Проект: Telegram-канал «Билет на стол» https://t.me/bilet_na_stol
  + бот [ссылка], партнёрство через Travelpayouts (trs 578817).

После whitelist получу OAuth-токен по ClientID b0ca9cd48f66420c9995c0776f2243a8
и буду соблюдать лимит ≤50 rps.

Нужны методы: hotels/suggest, hotels/search, hotels/hotel/offers, hotels/top-offers.
```

---

## Черновик первого письма (архив / Travelpayouts)

Ниже — исходный шаблон на `support@travelpayouts.com` (если снова понадобится через TP).  
Сейчас основной путь — чат Яндекса + whitelist.

**Кому:** `support@travelpayouts.com`  
**Тема:** Запрос доступа к API Яндекс Путешествий — проект Telegram «Билет на стол» (trs 578817)

```
Здравствуйте!

Прошу предоставить доступ к API Яндекс Путешествий
(раздел «Запрос данных по отелям»: hotels/search, hotels/hotel/offers, hotels/top-offers)
для партнёрского проекта в Travelpayouts.

Данные проекта
— Название: Билет на стол
— ID проекта (trs / source): 578817
— Marker: [ВАШ MARKER]
— Ресурс: Telegram-канал https://t.me/bilet_na_stol
— Бот: [ссылка на бота]
— Программа «Яндекс Путешествия» в каталоге: подключена

Контакты для OAuth / whitelist
— ФИО: [ФИО]
— Телефон: [+7…]
— Яндекс ID логин: [логин]
— Email @yandex: [имя]@yandex.ru

OAuth ClientID: b0ca9cd48f66420c9995c0776f2243a8

Спасибо!
[Имя]
```

---

## Заметки

- `TRAVELPAYOUTS_TOKEN` ≠ `YANDEX_TRAVEL_OAUTH` — разные штуки.
- URL из API Яндекса всё равно оборачивать в Links API (CPA + erid).
- HC Travelpayouts писал про ~5k MAU для контента — у тебя в ответе этого не было; если позже попросят статистику — честно сказать рост канала.

---

## Changelog

- 2026-09-28 — черновик + план; сначала думали «не слать без аудитории».
- 2026-09-28 — ответ Яндекса в чате: OAuth + whitelist + 50 rps; обновлён план «что сейчас».
