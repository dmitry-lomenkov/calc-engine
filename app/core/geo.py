"""Геокодинг места рождения + разрешение часового пояса с историческими смещениями.

Часовые пояса — главный источник ошибок. Здесь смещение берётся из базы IANA (zoneinfo),
которая авторитетно кодирует ВСЕ исторические переходы: декретное время СССР (с 1930),
летнее время 1981–1991, изменения смещений Новосибирска (1991/1993/2014/2016) и т.д.
Поэтому локальное время рождения → UTC считается точно для нужной эпохи.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import httpx
from timezonefinder import TimezoneFinder

from . import geocache, geonames

_tf = TimezoneFinder()
_GEOCODER = os.getenv("GEOCODER", "nominatim").strip().lower()  # nominatim = запасной геокодер

# Компактный газеттир: тест-города + крупные города. Для остального — timezonefinder по коорд.,
# либо явные координаты во входных данных. Формат: name → (lat, lon, iana_tz, display, country).
GAZETTEER = {
    "москва": (55.7558, 37.6173, "Europe/Moscow", "Москва", "RU"),
    "moscow": (55.7558, 37.6173, "Europe/Moscow", "Москва", "RU"),
    "санкт-петербург": (59.9311, 30.3609, "Europe/Moscow", "Санкт-Петербург", "RU"),
    "ленинград": (59.9311, 30.3609, "Europe/Moscow", "Ленинград (Санкт-Петербург)", "RU"),
    "saint petersburg": (59.9311, 30.3609, "Europe/Moscow", "Санкт-Петербург", "RU"),
    "новосибирск": (55.0084, 82.9357, "Asia/Novosibirsk", "Новосибирск", "RU"),
    "novosibirsk": (55.0084, 82.9357, "Asia/Novosibirsk", "Новосибирск", "RU"),
    "екатеринбург": (56.8389, 60.6057, "Asia/Yekaterinburg", "Екатеринбург", "RU"),
    "свердловск": (56.8389, 60.6057, "Asia/Yekaterinburg", "Свердловск (Екатеринбург)", "RU"),
    "мурманск": (68.9585, 33.0827, "Europe/Moscow", "Мурманск", "RU"),
    "murmansk": (68.9585, 33.0827, "Europe/Moscow", "Мурманск", "RU"),
    "владивосток": (43.1155, 131.8855, "Asia/Vladivostok", "Владивосток", "RU"),
    "калининград": (54.7104, 20.4522, "Europe/Kaliningrad", "Калининград", "RU"),
    "киев": (50.4501, 30.5234, "Europe/Kyiv", "Киев", "UA"),
    "минск": (53.9006, 27.5590, "Europe/Minsk", "Минск", "BY"),
    "алматы": (43.2220, 76.8512, "Asia/Almaty", "Алматы", "KZ"),
    "ташкент": (41.2995, 69.2401, "Asia/Tashkent", "Ташкент", "UZ"),
    "тбилиси": (41.7151, 44.8271, "Asia/Tbilisi", "Тбилиси", "GE"),
    "нью-дели": (28.6139, 77.2090, "Asia/Kolkata", "Нью-Дели", "IN"),
    "new delhi": (28.6139, 77.2090, "Asia/Kolkata", "Нью-Дели", "IN"),
    "delhi": (28.6139, 77.2090, "Asia/Kolkata", "Дели", "IN"),
    "ченнаи": (13.0827, 80.2707, "Asia/Kolkata", "Ченнаи", "IN"),
    "chennai": (13.0827, 80.2707, "Asia/Kolkata", "Ченнаи", "IN"),
    "мумбаи": (19.0760, 72.8777, "Asia/Kolkata", "Мумбаи", "IN"),
    "лондон": (51.5074, -0.1278, "Europe/London", "Лондон", "GB"),
    "london": (51.5074, -0.1278, "Europe/London", "Лондон", "GB"),
    "нью-йорк": (40.7128, -74.0060, "America/New_York", "Нью-Йорк", "US"),
    "new york": (40.7128, -74.0060, "America/New_York", "Нью-Йорк", "US"),
    "сидней": (-33.8688, 151.2093, "Australia/Sydney", "Сидней", "AU"),
    "sydney": (-33.8688, 151.2093, "Australia/Sydney", "Сидней", "AU"),
    "буэнос-айрес": (-34.6037, -58.3816, "America/Argentina/Buenos_Aires", "Буэнос-Айрес", "AR"),
    "buenos aires": (-34.6037, -58.3816, "America/Argentina/Buenos_Aires", "Буэнос-Айрес", "AR"),
}


class GeoError(Exception):
    pass


class GeoAmbiguous(Exception):
    """Несколько совпадений — нужен выбор пользователя."""
    def __init__(self, candidates: list[dict]):
        self.candidates = candidates
        super().__init__("ambiguous place")


def tz_for_coords(lat: float, lon: float) -> str | None:
    return _tf.timezone_at(lat=lat, lng=lon)


def geocode(place: str | None, lat: float | None, lon: float | None,
            tz_name: str | None, geoname_id: int | None = None) -> dict:
    """
    Возвращает подтверждаемый результат: город/координаты/часовой пояс.
    Приоритет: явные lat/lon → geoname_id → газеттир → GeoNames RU (с уточнением) →
    Nominatim (запасной) → просьба указать координаты.
    """
    if lat is not None and lon is not None:
        tz = tz_name or tz_for_coords(lat, lon)
        if not tz:
            raise GeoError("не удалось определить часовой пояс по координатам")
        return {"query": place, "city": place or f"{lat},{lon}", "lat": float(lat),
                "lon": float(lon), "tz": tz, "source": "explicit_coords"}

    if geoname_id is not None:
        g = geonames.by_id(int(geoname_id))
        if g:
            return {"query": place, **g, "tz": tz_name or g["tz"]}
        raise GeoError(f"geoname_id={geoname_id} не найден")

    if place:
        key = place.strip().lower()
        if key in GAZETTEER:
            la, lo, tz, disp, country = GAZETTEER[key]
            return {"query": place, "city": disp, "lat": la, "lon": lo,
                    "tz": tz_name or tz, "country": country, "source": "gazetteer"}
        # GeoNames RU (хранимый источник)
        gr = geonames.resolve(place)
        if gr.get("match"):
            m = gr["match"]
            return {"query": place, **m, "tz": tz_name or m["tz"]}
        if gr.get("candidates"):
            raise GeoAmbiguous(gr["candidates"])
        # кеш (результаты внешнего геокодера)
        cached = geocache.get(place)
        if cached:
            return {"query": place, **cached, "tz": tz_name or cached["tz"]}
        # внешний геокодер (по флагу)
        if _GEOCODER == "nominatim":
            res = _nominatim(place)
            if res:
                geocache.put(place, res["city"], res["lat"], res["lon"], res["tz"], "nominatim")
                return {"query": place, **res, "tz": tz_name or res["tz"], "source": "nominatim"}
        raise GeoError(
            f"город '{place}' не найден в справочнике; передайте координаты (lat/lon), "
            "используйте известный город или включите GEOCODER=nominatim")
    raise GeoError("укажите place или lat/lon")


def _nominatim(place: str) -> dict | None:
    """OpenStreetMap Nominatim. Условия: ≤1 запрос/сек, обязательный User-Agent, без массовых
    выгрузок (https://operations.osmfoundation.org/policies/nominatim/). Бесплатно.
    Результат кешируется в БД, поэтому повторные запросы не идут наружу."""
    try:
        r = httpx.get("https://nominatim.openstreetmap.org/search",
                      params={"q": place, "format": "json", "limit": 1},
                      headers={"User-Agent": "jyotisha365/0.2 (geocoding)"}, timeout=10.0)
        arr = r.json()
        if not arr:
            return None
        it = arr[0]
        lat, lon = float(it["lat"]), float(it["lon"])
        tz = tz_for_coords(lat, lon)
        return {"city": it.get("display_name", place).split(",")[0], "lat": lat, "lon": lon, "tz": tz}
    except Exception:
        return None


def to_utc(local_naive: datetime, tz_name: str) -> tuple[datetime, float, bool]:
    """
    Локальное «наивное» время рождения + IANA-пояс → (UTC naive, смещение_часы, ambiguous).
    Смещение соответствует ЭПОХЕ рождения (историческое). fold=0 по умолчанию.
    """
    tz = ZoneInfo(tz_name)
    aware = local_naive.replace(tzinfo=tz)
    off = aware.utcoffset()
    offset_hours = off.total_seconds() / 3600.0 if off else 0.0
    # проверка неоднозначности (перевод часов): сравнить fold=0 и fold=1
    alt = local_naive.replace(tzinfo=tz, fold=1)
    ambiguous = alt.utcoffset() != off
    utc = aware.astimezone(timezone.utc).replace(tzinfo=None)
    return utc, offset_hours, ambiguous
