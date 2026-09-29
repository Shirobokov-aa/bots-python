# Сценарии мультибота (черновик)

Не лок в `agreed.md`. Идея: **один бот / одно ядро**, меню сценариев поверх `catalog.json`.

## Этап 1 (решение 2026-09-28)

Фокус: **автовладелец** — проверка авто, штрафы, ОСАГО/КБМ, долги на платниках, прочее по ТС.  
Не этап 1: KYC людей, контрагенты, недвижимость, медкнижки (этап 2+).

Продуктовое имя черновое: AutoCheck / «проверка авто» (ideals **#52** + штрафы).

---

## Архитектура (набросок)

```
TG bot
  └─ scenarios/*.yaml   # ввод → список api+type → шаблон ответа
  └─ client api-cloud    # общий HTTP + token + retry
  └─ catalog.json       # цены → COGS / прайс юзеру
```

Один токен api-cloud. Deep-link: `t.me/bot?start=fines` и т.п.

---

## Этап 1 — сценарии автовладельца

| Prio | ID | Юзер вводит | Методы (минимум) | Себест. ≈ | Продажа ≈ |
|------|----|-------------|------------------|-----------|-----------|
| P0 | `fines` | номер + СТС | gibdd.fines (+ finesPhoto) | ~0.8₽ | 29₽ / подписка пуш |
| P0 | `auto_preview` | VIN / номер | vin_converter?, photos/nomerogram, car_price, recalls.vin | 2–3₽ | free / 1₽ |
| P0 | `auto_report` | VIN / номер | restrict, wanted, dtp, eaisto, notary, fedresurs, fts.auto, epts.pts, rsa.osago, fgis_taxi/taxi_history, recalls.vin | 6–10₽ + ?ГИБДД | 99₽ |
| P1 | `osago_kbm` | данные водителя/ТС | rsa.kbm, rsa.osago | 1.00₽ | 29₽ |
| P1 | `avtodor` | номер | avtodor.payCheck | 0.20₽ | 19₽ |
| P1 | `driver_check` | ВУ + ФИО | gibdd.driverv2 | 0.50₽ | 49₽ |
| P2 | `truck_msk` | номер | mos_transport.pass, rnis | 1.20₽ | 49₽ |
| P2 | `taxi_check` | номер | fgis_taxi.search + taxi_history.search | ~0.87₽ | 29₽ |

**MVP порядок:** `fines` → `auto_preview` → `auto_report` → оплата. Остальное — меню после живого ядра.

---

## Этап 2+ (не трогать сейчас)

| ID | Зачем | Когда |
|----|-------|-------|
| `person_debts` | ФССП ФЛ | после авто-MVP |
| `company_dd` | контрагент | после авто-MVP |
| `selfemployed` / `passport` / `dover` / `medbook` | KYC / HR | позже |
| `realty` | квартира | позже |

---

## Принципы

1. Сценарий = YAML/JSON: `inputs`, `steps[]`, `price_user`.  
2. Fail одного step ≠ fail всего.  
3. Кэш по VIN/номеру TTL 24ч.  
4. `driver_check` — ПДн: согласие + короткий TTL (даже в этапе 1).  
5. Один бот, пока меню не раздуется.

## Блокер до кода

- Токен / доступ api-cloud (регистрация). Если support ответил ограничением — вставить сюда текст ответа.
- Уточнить цены ГИБДД без явной строки на tarif (`restrict`/`fines`/…).

## Решение позже

- Лок в `agreed` после токена + первых живых ответов API  
- Отдельный бот vs меню внутри мультибота
