# calc_engine — ведический астрологический расчётный движок

Изолированный микросервис ведической (джйотиша) астрологии: натальные карты, панчанга,
даши, транзиты, геокодинг. **FastAPI + [pyswisseph](https://github.com/astrorigin/pyswisseph)**
(обёртка над [Swiss Ephemeris](https://www.astro.com/swisseph/)).

Это расчётное ядро проекта **[JYOTISHA 365](https://jyotisha365.ru)**, вынесенное в отдельный
сервис с собственной лицензией, чтобы его можно было опубликовать и использовать независимо.

> **Лицензия: GNU AGPL-3.0** (см. [LICENSE](LICENSE) и [NOTICE](NOTICE)).
> Swiss Ephemeris распространяется под AGPL-3.0 либо коммерческой лицензией Astrodienst;
> этот сервис использует вариант AGPL-3.0, поэтому и сам распространяется под AGPL-3.0.

## Параметры расчётов

- Зодиак: **сидерический**
- Аянамша: **Лахири** (`AYANAMSHA=lahiri`; поддерживаются также `raman`, `krishnamurti`)
- Дома: **Whole Sign** (`HOUSE_SYSTEM=whole_sign`)
- Лунные узлы: **средние** (`NODE_TYPE=mean`)
- Восход/заход: верхний край диска Солнца + атмосферная рефракция (правило drikpanchang)

Сверено с drikpanchang: планеты и узлы — расхождение <1′; восход/заход и окончания
титхи/накшатры — <1 минуты (Москва, Новосибирск и др.).

## Основные эндпоинты

| Метод | Путь | Назначение |
|---|---|---|
| `GET`  | `/health` | статус сервиса + доступность Swiss Ephemeris |
| `POST` | `/v1/natal` | натальная карта D1/D9: грахи (долгота, раши, накшатра+пада, ретро), лагна, навамса, вимшоттари-даши; `sun_tropical` — тропический (западный) знак Солнца |
| `POST` | `/v1/panchanga` | панчанга на дату/место: титхи, накшатра, йога, карана, вара, восход/заход, мухурты |
| `POST` | `/v1/personal_day` | тара-бала, чандраштама, накшатра/титхи дня относительно натальной карты |
| `POST` | `/v1/transits` | текущие транзиты медленных планет |
| `POST` | `/v1/sky_events` / `/v1/sky_sequence` | астрособытия (санкранти, ретроградности, затмения) и последовательность смен |
| `POST` | `/v1/geocode` | геокодинг места рождения + часовой пояс с историческими смещениями |

Схемы запросов/ответов — в [`app/schemas.py`](app/schemas.py).

## Запуск

### Docker

```bash
docker build -t calc_engine .
# положите файлы эфемерид в app/ephe (см. ниже) — они копируются в образ при сборке
docker run --rm -p 127.0.0.1:8130:8130 calc_engine
curl -s http://127.0.0.1:8130/health
```

### Локально

```bash
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8130
```

### Эфемериды Swiss Ephemeris

Файлы данных (`*.se1`) **не входят в репозиторий** (см. `.gitignore`). Скачайте нужный
диапазон и положите в `app/ephe/`. Для диапазона 1800–2400 достаточно:
`sepl_18.se1`, `semo_18.se1`, `seas_18.se1` — с
[ftp.astro.com/pub/swisseph/ephe](https://www.astro.com/ftp/swisseph/ephe/) (или из пакета pyswisseph).
Путь к папке — переменная `EPHE_PATH` (по умолчанию `app/ephe`).

## Переменные окружения

| Переменная | По умолчанию | Назначение |
|---|---|---|
| `AYANAMSHA` | `lahiri` | аянамша |
| `HOUSE_SYSTEM` | `whole_sign` | система домов |
| `NODE_TYPE` | `mean` | тип лунных узлов |
| `EPHE_PATH` | `app/ephe` | путь к файлам эфемерид |

Геокодинг по офлайн-базе GeoNames опционален: загрузка — `tools/load_geonames.sh`
(данные GeoNames — [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)).

## Тесты

```bash
python tests/run_reference.py        # эталонные карты
python tests/compare_drikpanchang.py # сверка с drikpanchang
```

## Благодарности

- [Swiss Ephemeris](https://www.astro.com/swisseph/) — Astrodienst AG (AGPL-3.0)
- [GeoNames](https://www.geonames.org/) — CC BY 4.0
