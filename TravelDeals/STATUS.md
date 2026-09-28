# TravelDeals — статус

Канал: [@bilet_na_stol](https://t.me/bilet_na_stol) («Билет на стол»).

## В работе
- [ ] P9 Яндекс API: whitelist логина → OAuth → тест → код цен. → commit: `feat(traveldeals): yandex travel hotel prices`
- [ ] Деплой antru: workflow + bootstrap `/opt/bots/traveldeals`. → commit: `ci(traveldeals): deploy workflow and docker`

## Очередь
- [ ] Вставить закреп/описание из `docs/ideas/C3-channel-pin.md` в канал (руками). → commit: —
- [ ] Level.Travel как отдельный провайдер туров. → commit: позже
- [ ] Заполнить «Мои программы» в `docs/travelpayouts/programs.md` после логина в каталог. → commit: `docs(traveldeals): my programs list`
- [ ] Чеклист закона о рекламе в ЛК (форма ЕРИР + пометки в постах). → commit: позже

## Сделано
### 2026-09-28
- **Шпаргалка Yandex Travel API.** Host, OAuth, limits, search/suggest/offers, curl, план бота → `yandex-travel-api.md`. → commit: `docs(traveldeals): yandex travel api cheatsheet`
- **Ответ Яндекса по API.** Не отказ: аккаунт + OAuth + ≤50 rps; план whitelist в `yandex-api-request.md`. → commit: `docs(traveldeals): yandex api whitelist path`
- **Полировка MVP 1–7.** Даты отеля=вылет; спокойные captions; Hotellook/HotelDeal вычищены; C3 текст; чеклист TRS/программ; ~30 городов; `routes.yaml` шире. → commit: `feat(traveldeals): polish mvp without hotel prices`
- **Заявка Яндекс (черновик).** Письмо + план в `yandex-api-request.md`. → commit: `docs(traveldeals): yandex api request draft`
- **Docs Travelpayouts.** `docs/travelpayouts/`: карта API, программы, hotels API, закон о рекламе. → commit: `docs(traveldeals): travelpayouts api programs hotels ad-law`
- **Отели deeplink (P8).** Hotellook убран; `/hotel`+канал → Островок/Яндекс через Links API. → commit: `feat(traveldeals): hotel deeplink fallback`
- **Живой прогон.** Token/marker/канал; пост в `@bilet_na_stol`. → commit: —
- **Лок M1+M2.** Карточки ideas. → commit: `docs(traveldeals): lock M1 M2 ideas`
- **Docs идей.** `docs/ideas.md` + шаблон. → commit: `docs(traveldeals): ideas bank and locked template`
### 2026-09-22
- **MVP код:** поиск, алерты, воркер канала, дедуп, тесты. → commit: `feat(traveldeals): mvp bot channel and deals`
- **Лок #10** в `agreed.md`. → commit: `docs(agreed): lock traveldeals in progress`
