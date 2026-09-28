# Яндекс Путешествия — Travel Partners API (шпаргалка)

Снято с офиц. доков (2026-09-28) + ответ саппорта в чате.  
Полные страницы: [корень](https://yandex.ru/dev/travel-partners-api/doc/ru/),  
[авторизация](https://yandex.ru/dev/travel-partners-api/doc/ru/authorization),  
[старт](https://yandex.ru/dev/travel-partners-api/doc/ru/getting-started),  
[лимиты](https://yandex.ru/dev/travel-partners-api/doc/ru/limits).

Заявка / whitelist: [yandex-api-request.md](yandex-api-request.md).

---

## 1. Что это

White-label API отелей: сниппеты, цены, офферы, ссылки на бронь.  
База (host):

```
https://whitelabel.travel.yandex-net.ru
```

Обмен: HTTP REST + JSON.  
Заголовок на **каждый** запрос:

```
Authorization: OAuth <token>
Content-Type: application/JSON
```

---

## 2. Доступ (пока ждём whitelist)

| Шаг | Действие | Источник |
|-----|----------|----------|
| 1 | Аккаунт Яндекса владельца + 2FA | [authorization](https://yandex.ru/dev/travel-partners-api/doc/ru/authorization) |
| 2 | Логин в whitelist (~сутки, письмо на почту Яндекс ID) | тот же + [getting-started](https://yandex.ru/dev/travel-partners-api/doc/ru/getting-started) |
| 3 | OAuth token, ClientID `b0ca9cd48f66420c9995c0776f2243a8` | |
| 4 | Тест: `GET /hotels/hotel/?hotel_id=1019057204` | getting-started |
| 5 | Партнёр Яндекс Путешествий (через TP ок, если приняли) | [партнёрская сеть](https://yandex.ru/support/travel-distr/partner.html) |

OAuth URL:

```
https://oauth.yandex.ru/authorize?response_type=token&client_id=b0ca9cd48f66420c9995c0776f2243a8
```

Token живёт **1 год**. В `.env`: `YANDEX_TRAVEL_OAUTH=` — **не путать** с `TRAVELPAYOUTS_TOKEN`.

---

## 3. Лимиты

Из [limits](https://yandex.ru/dev/travel-partners-api/doc/ru/limits):

| Ограничение | Квота | При превышении |
|-------------|-------|----------------|
| Запросы с одного IP | **50 / сек** | `429 Too Many Requests`, пока счётчик за секунду < 50 |

Для Telegram-бота (редкие `/hotel`, тик канала) — запас огромный.  
Не крутить polling в tight loop без sleep.

---

## 4. Методы — что нам нужно

### Приоритет для «Билет на стол»

| Приоритет | Метод | URL path | Зачем |
|-----------|-------|----------|-------|
| P0 | suggest | `GET /hotels/suggest/` | Город → `geo_id` (IATA у нас ≠ geo_id) |
| P0 | search | `GET /hotels/search/` | Список отелей **с ценами** (`top_offers[].price`) |
| P1 | top_offers | `GET /hotels/top_offers` | Цены пачкой по `hotel_ids` (до 100) |
| P1 | hotel/offers | `GET /hotels/hotel/offers/` | Номера + цены + `booking_url` одного отеля |
| P2 | hotel | `GET /hotels/hotel/` | Карточка без цен (тест из старта) |
| P2 | selection | `GET /hotels/selection/` | Сниппеты + `top_price` (слабее search) |
| P2 | hotel/images | `GET /hotels/hotel/images/` | Фото |
| — | booking/* | бронь/оплата/отмена | **Не сейчас** — уводим кликом на Яндекс |

Доки методов:

- [suggest](https://yandex.ru/dev/travel-partners-api/doc/ru/suggest)
- [search](https://yandex.ru/dev/travel-partners-api/doc/ru/search)
- [top-offers](https://yandex.ru/dev/travel-partners-api/doc/ru/top-offers)
- [hotel-offers](https://yandex.ru/dev/travel-partners-api/doc/ru/hotel-offers)
- [hotel](https://yandex.ru/dev/travel-partners-api/doc/ru/hotel)
- [selection](https://yandex.ru/dev/travel-partners-api/doc/ru/selection)

---

## 5. Контракты (кратко)

### 5.1 suggest — регион / отель по строке

```
GET /hotels/suggest/?query=Анталья&region_limit=5&hotel_limit=0
```

Ответ: `regions[].geo_id`, `type` (`CITY`/`REGION`/…), `name`.  
**Нам:** `query=name_ru` → взять первый `CITY` → сохранить `geo_id` в справочник городов.

### 5.2 search — выдача с ценами (главный)

Обязательные: `geo_id`, `checkin_date`, `checkout_date`, `adults`.

```
GET /hotels/search/?geo_id=213&checkin_date=2026-10-01&checkout_date=2026-10-08
  &adults=2&order_by=price-asc&page_limit=5
```

Пример из доков: `geo_id=213` = Москва (Яндекс geo).

Полезные опции:

| Параметр | Смысл |
|----------|--------|
| `order_by=price-asc` | дешёвые первые |
| `page_limit` | default 10, max 50 |
| `page_token` | следующая страница (`next_page_token`) |
| `min_price` / `max_price` | ₽ **за ночь** |
| `stars=3\|4\|5` | звёзды |
| `meal_type=RO\|BB\|…` | питание |
| `affiliate_clid` | clid Дистрибуции (если выдали) |

Ответ (важное):

```json
{
  "complete": true,
  "hotel_snippets": [
    {
      "hotel_id": "...",
      "name": "...",
      "stars": 4,
      "rating": "4.5",
      "top_offers": [
        { "price": { "value": 53500, "currency": "RUB" }, "meal_type": { "id": "RO" } }
      ],
      "landing_url": "https://travel.yandex.ru/hotels/..."
    }
  ],
  "next_page_token": "50"
}
```

- `price.value` — сумма предложения (в примерах — за период; фильтры min/max — **за ночь**). В UI писать аккуратно: «от N ₽» + даты.
- `landing_url` — страница отеля с датами → **обернуть в Links API** (CPA TP).
- `complete: false` → polling: повторить запрос, пока `true` (с паузой).

### 5.3 top_offers — цены пачкой

```
GET /hotels/top_offers?checkin_date=...&checkout_date=...&adults=2&hotel_ids=id1,id2
```

Ответ: `{ hotel_id, price: { value, currency } }[]`.  
`adults` обязателен. До 100 id.

### 5.4 hotel/offers — детали одного отеля

```
GET /hotels/hotel/offers/?hotel_id=...&checkin_date=...&checkout_date=...&adults=2
```

В ответе `rooms[].offers[].price` + `booking_url` (редирект Яндекса).  
Тоже polling через `complete`.

### 5.5 hotel — smoke-тест

```
GET /hotels/hotel/?hotel_id=1019057204
```

Без дат/цен — проверка, что OAuth жив.

---

## 6. `affiliate_clid` vs Travelpayouts

Яндекс API знает **clid Дистрибуции**.  
Мы сидим в **Travelpayouts** (`trs=578817`, marker, Links API).

Практичный путь для бота:

1. Брать `landing_url` / `booking_url` из ответа API.
2. Гнать через уже существующий `affiliate_wrap()` → партнёрская ссылка TP (+ erid когда форма ок).
3. Если Яндекс выдаст отдельный `affiliate_clid` — передавать в query; иначе default clid партнёра.

Не подставлять TP `marker` в `affiliate_clid` вслепую.

---

## 7. План интеграции в бот (когда токен есть)

```
.env
  YANDEX_TRAVEL_OAUTH=...

cities.py
  + yandex_geo_id: int | None
  (или резолв через suggest на лету + кэш)

yandex_travel.py (новый клиент)
  suggest(query) → geo_id
  search(geo_id, check_in, check_out, adults=2, order_by=price-asc, limit=3)
  wrap landing_url → Links API

/hotel и канал
  вместо «только кнопки» → «от N ₽ · 3 отеля» + кнопки
  даты уже = вылет (hotel_dates_for_flight)
```

Минимальный happy-path после whitelist:

1. curl hotel smoke  
2. curl suggest «Анталья» → geo_id  
3. curl search price-asc page_limit=3  
4. вставить token в `.env` → код

---

## 8. Чеклист curl (после токена)

```bash
TOKEN='…'   # из OAuth

# smoke
curl -sS -H "Authorization: OAuth $TOKEN" \
  'https://whitelabel.travel.yandex-net.ru/hotels/hotel/?hotel_id=1019057204' | head

# город → geo_id
curl -sS -H "Authorization: OAuth $TOKEN" \
  --get 'https://whitelabel.travel.yandex-net.ru/hotels/suggest/' \
  --data-urlencode 'query=Анталья' \
  --data-urlencode 'region_limit=5' \
  --data-urlencode 'hotel_limit=0'

# цены (подставь geo_id и даты)
curl -sS -H "Authorization: OAuth $TOKEN" \
  'https://whitelabel.travel.yandex-net.ru/hotels/search/?geo_id=GEO&checkin_date=2026-10-15&checkout_date=2026-10-22&adults=2&order_by=price-asc&page_limit=3'
```

---

## 9. Риски

- Whitelist ещё не пришёл — все запросы 401/403.
- `price.value` vs «за ночь» в фильтрах — не путать в тексте поста.
- Polling без backoff → риск 429 (маловероятно при 50 rps, но грязно).
- Бронь внутри API не делаем — только витрина + клик.
- Token истечёт через год — календарь.

---

## Changelog

- 2026-09-28 — собрана шпаргалка из authorization / getting-started / limits + search/suggest/top-offers/hotel-offers.
