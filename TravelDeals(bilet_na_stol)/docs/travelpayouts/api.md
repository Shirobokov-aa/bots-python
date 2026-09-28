# API и данные Travelpayouts

Источник категории: https://support.travelpayouts.com/hc/ru/categories/200358578  
Сводка брендов с API/фидами: https://support.travelpayouts.com/hc/ru/articles/20384016664594

У каждого бренда свои условия доступа (трафик, тематика, заявка в support).  
API ≠ программа: программа даёт CPA-ссылки; API/фид — данные (цены, каталоги).

---

## 1. API самой платформы Travelpayouts

| API | Зачем | Статья |
|-----|--------|--------|
| Партнёрские ссылки | Прямой URL бренда → партнёрская (CPA + erid). Уже в боте (`LINKS_API`) | [25289759198226](https://support.travelpayouts.com/hc/ru/articles/25289759198226) |
| Статистика бронирований | Отчёты по конверсиям программ | [360019864079](https://support.travelpayouts.com/hc/ru/articles/360019864079) |
| Баланс и выплаты | Баланс / выплаты | [5169505760402](https://support.travelpayouts.com/hc/ru/articles/5169505760402) |
| IATA-код | Определение IATA | [360002755812](https://support.travelpayouts.com/hc/ru/articles/360002755812) |
| Гео по IP | Локация пользователя | [205895898](https://support.travelpayouts.com/hc/ru/articles/205895898) |
| IATA из фразы | Город из поисковой строки | [203955773](https://support.travelpayouts.com/hc/ru/articles/203955773) |

### Links API (используем сейчас)

- Endpoint: `POST https://api.travelpayouts.com/links/v1/create`
- Header: `X-Access-Token: <TRAVELPAYOUTS_TOKEN>`
- Body: `trs` (ID проекта), `marker`, `shorten`, `links[{url, sub_id?}]`
- Лимит: 100 req/min на маркер; ≤10 URL за запрос
- Только длинные URL бренда (не короткие)
- Не работает для: Т-Банк, Сравни.ру, Альфа Банк, Park&Fly, Ticketmaster, Expedia UK, HolidayTaxis, inDrive
- Проект должен быть **подписан** на программу бренда

Пример из доки TP (Яндекс отели):

```json
{
  "trs": 197987,
  "marker": 339296,
  "shorten": true,
  "links": [
    {
      "url": "https://travel.yandex.ru/hotels/moscow/beta-izmailovo/?adults=2&checkinDate=2025-03-24&checkoutDate=2025-03-29",
      "sub_id": "example"
    }
  ]
}
```

Ответ: `partner_url` вида `https://yandex.tp.st/...`

Token: Профиль → вкладка API-ключ.  
TRS: список проектов / `?source=` в Tools (у нас `578817`).

---

## 2. Авиа (Aviasales)

Два разных продукта:

| Тип | Суть | Доступ |
|-----|------|--------|
| API **данных** | Популярные направления, низкие цены (кэш/агрегаты) | Партнёры; условия в [203956083](https://support.travelpayouts.com/hc/ru/articles/203956083) |
| API **поиска** realtime | Живой поиск + сложные маршруты | Отдельный доступ, md5 signature |

Ключевые статьи:

- Данные для партнёров: [203956163](https://support.travelpayouts.com/hc/ru/articles/203956163)
- GraphQL: [4417975783314](https://support.travelpayouts.com/hc/ru/articles/4417975783314)
- Фид данных: [360018907280](https://support.travelpayouts.com/hc/ru/articles/360018907280)
- Автокомплит стран/городов/аэропортов: [360002322572](https://support.travelpayouts.com/hc/ru/articles/360002322572)
- Доступ к поиску: [210995808](https://support.travelpayouts.com/hc/ru/articles/210995808)
- Поиск realtime / сложные маршруты: [30565016140434](https://support.travelpayouts.com/hc/ru/articles/30565016140434)
- Signature md5: [210996008](https://support.travelpayouts.com/hc/ru/articles/210996008)
- Правила поиска: [34788165535250](https://support.travelpayouts.com/hc/ru/articles/34788165535250)
- Отличия видов API: [FAQ](https://support.travelpayouts.com/hc/ru/articles/) — «У вас несколько видов API…»
- Лимиты / токен / языки — секция FAQ Aviasales

Для канала «цены авиа» обычно хватает **API данных** (как в MVP). Realtime — тяжелее по доступу и лимитам.

---

## 3. Отели

Hotellook API **исчез** из раздела. Живые варианты:

| Бренд | Цены? | Порог / доступ |
|-------|-------|----------------|
| **Яндекс Путешествия** | Да (`search`, `hotel/offers`, `top-offers`) | Контент, от ~5 000 MAU; заявка + OAuth `@yandex` |
| **Суточно.ру** | Да (объекты с ценами, cheapest rooms) | Заявка в support; рассмотрение ~до 3 недель |

Подробно: [hotels-api.md](hotels-api.md).

---

## 4. Организация поездок (жд / автобус / трансфер)

| Бренд | Тип | Ссылка |
|-------|-----|--------|
| Tutu.ru | API + фид популярных маршрутов | [API](https://support.travelpayouts.com/hc/ru/articles/360020147791) / [фид](https://support.travelpayouts.com/hc/ru/articles/115001440551) |
| Omio | Фид | [360024389872](https://support.travelpayouts.com/hc/ru/articles/360024389872) |
| intui.travel | API трансферов (поиск с ценами, каталог маршрутов, deeplink заказа) | [360016804119](https://support.travelpayouts.com/hc/ru/articles/360016804119) |
| GetTransfer | API (поиск, заявка, оплата на стороне партнёра) | [360016375920](https://support.travelpayouts.com/hc/ru/articles/360016375920) |
| Суточно.ру | Фид объектов (отдельно от API) | [360028511592](https://support.travelpayouts.com/hc/ru/articles/360028511592) |

Tutu: API для виджета/таблиц расписания — **не realtime-цены** для поисковых форм.

---

## 5. Экскурсии

| Бренд | Тип |
|-------|-----|
| YouTravel.me | API |
| Большая Страна | API |
| Tiqets | Фид |
| Sputnik8 | API |
| WeGoTrip | API (+ карточки / ссылка на оплату) |
| Трипстер | API (города, страны, категории, экскурсии) |
| Tezeks | API (экскурсии + трансферы + справочники) |

Статьи: секция «API и данные экскурсий» в категории 200358578.

---

## 6. Пакетные туры

| Бренд | Тип | Заметки |
|-------|-----|---------|
| Level.travel | API + фид | Справочники, поиск, горящие; фид цен ~каждые 30 мин |
| Travelata | API + фид | Туры |
| Tezeks | API | См. экскурсии/туры выше |

Level: [API](https://support.travelpayouts.com/hc/ru/articles/360019529079) / [фид](https://support.travelpayouts.com/hc/ru/articles/360019467880) — кандидат на P3 / очередь STATUS (отдельный провайдер туров).

---

## 7. eSIM

- Airalo — фид данных: [17131439719826](https://support.travelpayouts.com/hc/ru/articles/17131439719826)

---

## 8. Что релевантно боту сейчас

| Уже / план | API |
|------------|-----|
| Авиа-цены в канале/боте | Aviasales data API (токен+marker) |
| Отели без цен (P8) | Deeplink + **Links API** (trs=578817) |
| Отели **с ценами** (надежда) | Яндекс Travel API или Суточно — заявка, пороги |
| Туры | Level.travel API/фид (очередь) |
| Маркировка | Links API вшивает erid при заполненной форме «Закон о рекламе» |

Маркировка API/White Label/Travel App **не нужна** — только ссылки и виджеты. См. [ad-law.md](ad-law.md).
