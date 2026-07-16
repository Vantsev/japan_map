# Keikenchi — Japan Lifetime Score 🗾

Веб-версия «отметь посещённые префектуры Японии и меряйся баллами».
Каждой из 47 префектур ставишь балл 0–5 (0 Unexplored → 5 Resided), сумма = Lifetime Score (макс 235).

Живая карта, зум/пан, счётчик визитов, облачное сохранение и комнаты-лидерборды — без регистрации.

## Фичи

- **Карта 47 префектур** — клик красит балл (кисть из легенды), клик тем же уровнем сбрасывает.
- **Зум/пан** — колесо, пинч, драг, кнопки `+ / − / ⤢`.
- **Счётчик визитов** — правый клик / долгий тап → степпер `− N +`, бейдж `×N` на карте. Балл (качество) и число визитов (частота) раздельно.
- **Заметки** — в том же попапе: цель поездки, отель, что видел.
- **Подписи префектур** — тоггл «Названия» (кандзи, масштабируются с зумом).
- **Экспорт PNG** — чистая картинка карта+счёт, без интерфейса.
- **Облако + комнаты** — «Сохранить в облако» даёт ссылку; создаёшь комнату, кидаешь друзьям код → лидерборд по баллам. Логина нет: у карты публичный `id` и секретный `editKey`.

Всё это — ответ на жалобы к оригинальному приложению (реклама поверх кнопок, нет детализации, «ночевал но по работе», мелкие названия, потеря данных при смене телефона). У нас рекламы нет, данные в облаке, визиты отдельно от балла.

## Стек

- **Фронт**: один самодостаточный `public/index.html` (SVG-карта, данные инлайн). Генерится из `build.py`.
- **API**: Cloudflare Pages Functions — `functions/api/[[path]].js`.
- **БД**: Cloudflare D1 (`schema.sql`).

## Данные карты

`japan.min.json` — 47 префектур, упрощённая геометрия (собственный ring-aware Douglas-Peucker) из [`dataofjapan/land`](https://github.com/dataofjapan/land). Исходный `japan.geojson` (13 МБ) в репо не хранится — качается заново и упрощается через `simplify.py`:

```bash
curl -sL -o japan.geojson https://raw.githubusercontent.com/dataofjapan/land/master/japan.geojson
python3 simplify.py 0.0008   # eps в градусах: меньше = глаже берег, больше файл
```

Окинава выносится во врезку (верх-лево), главные острова масштабируются по своему bbox — иначе далёкий юг сжимает всю карту.

## Разработка

```bash
python3 build.py                                    # собрать public/index.html
npx wrangler d1 execute keikenchi --local --persist-to .wrangler-state --file schema.sql
npx wrangler pages dev public --persist-to .wrangler-state
```

Без бэкенда (только карта, localStorage) — просто открой `public/index.html` в браузере.
Облако/комнаты работают только по http(s), не через `file://`.

## Деплой

См. `deploy.sh` (Cloudflare) — или вручную:

```bash
npx wrangler login
npx wrangler d1 create keikenchi                    # id → в wrangler.toml
npx wrangler d1 execute keikenchi --remote --file schema.sql
npx wrangler pages deploy public --project-name keikenchi
```

## API

| Метод | Путь | Тело / заголовок | Ответ |
|---|---|---|---|
| POST | `/api/map` | `{name,data}` | `{id,editKey,score}` |
| GET | `/api/map/:id` | — | `{id,name,data,score,updated_at}` |
| PUT | `/api/map/:id` | `{name,data}` + `x-edit-key` | `{id,score}` |
| POST | `/api/room` | `{name}` | `{id}` |
| POST | `/api/room/:id/join` | `{mapId}` | `{ok:true}` |
| GET | `/api/room/:id` | — | `{id,name,members:[{id,name,score}]}` |

`data` = `"<47 баллов>-<47 счётчиков base36>"`.

## Роадмап

- MVP-3: детализация до городов/районов (частая просьба в отзывах).
- Отзывы о местах: точка появляется на карте только после отзыва (парсинг OSM/Overpass).
- Ачивки.
