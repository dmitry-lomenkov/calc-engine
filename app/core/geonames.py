"""Геокодер на базе GeoNames RU (хранится в БД: geo.places + geo.place_names + geo.admin1_ru).

Источник координат — полная выгрузка GeoNames по России (CC BY 4.0). Часовой пояс берётся
из GeoNames (колонка timezone). При нескольких совпадениях возвращается список для уточнения
(с районом/областью), а не ошибка.
"""

from __future__ import annotations

import os

_DSN = (os.getenv("DATABASE_URL", "") or "").replace("postgresql+psycopg://", "postgresql://")

# упрощённая транслитерация кириллицы для сопоставления квалификаторов с alternatenames
_TRANSLIT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh",
    "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "kh", "ц": "ts",
    "ч": "ch", "ш": "sh", "щ": "shch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}
_STOP = ("район", "р-н", "область", "обл", "обл.", "край", "республика", "г.", "город",
         "rayon", "district", "oblast", "kray", "krai", "respublika")


def _translit(s: str) -> str:
    return "".join(_TRANSLIT.get(ch, ch) for ch in s.lower())


def _norm_qualifier(q: str) -> str:
    q = q.strip().lower()
    for st in _STOP:
        q = q.replace(st, "")
    return q.strip(" .,")


def _conn():
    import psycopg
    return psycopg.connect(_DSN, connect_timeout=3)


def by_id(geoname_id: int) -> dict | None:
    if not _DSN:
        return None
    try:
        with _conn() as c:
            row = c.execute(
                "SELECT id,name,lat,lon,tz,region_ru,district,alternatenames,coalesce(population,0) "
                "FROM geo.places WHERE id=%s", (geoname_id,)).fetchone()
    except Exception:
        return None
    if not row:
        return None
    return _fmt(row)


def nearest(lat: float, lon: float, radius_deg: float = 0.1) -> dict | None:
    """Самое населённое место GeoNames рядом с координатами (для базового размера звезды
    по населению города). Без привязки к названию — надёжно для газеттир-городов."""
    if not _DSN:
        return None
    try:
        with _conn() as c:
            row = c.execute(
                "SELECT id,name,lat,lon,tz,region_ru,district,alternatenames,coalesce(population,0) "
                "FROM geo.places WHERE lat BETWEEN %s AND %s AND lon BETWEEN %s AND %s "
                "ORDER BY population DESC NULLS LAST LIMIT 1",
                (lat - radius_deg, lat + radius_deg, lon - radius_deg, lon + radius_deg)).fetchone()
    except Exception:
        return None
    return _fmt(row) if row else None


def _is_russian(tok: str) -> bool:
    """Токен целиком на русских буквах (исключаем укр./бел. і ї є ґ ў и латиницу)."""
    letters = [ch for ch in tok.lower() if ch.isalpha()]
    return bool(letters) and all(("а" <= ch <= "я") or ch == "ё" for ch in letters)


def _fmt(row) -> dict:
    _id, name, lat, lon, tz, region_ru, district, alt = row[:8]
    population = int(row[8]) if len(row) > 8 and row[8] is not None else 0
    # человекочитаемое имя: предпочитаем ЧИСТО русское из alternatenames (не укр. «Іскітім»)
    ru = None
    for tok in (alt or "").split(","):
        t = tok.strip()
        if _is_russian(t):
            ru = t; break
    return {"geoname_id": _id, "city": ru or name, "lat": float(lat), "lon": float(lon),
            "tz": tz, "region": region_ru, "district": district, "population": population,
            "source": "geonames"}


def resolve(place: str) -> dict:
    """Возврат: {'match': {...}} | {'candidates': [...]} | {'none': True}.
    place может содержать квалификаторы через запятую: 'Дубровка, Маслянинский район, ...'."""
    if not _DSN:
        return {"none": True}
    parts = [p.strip() for p in place.split(",") if p.strip()]
    if len(parts) == 1:
        words = parts[0].split()
        name = words[0]
        qualifiers = [_norm_qualifier(w) for w in words[1:]]
    else:
        name = parts[0]
        qualifiers = [_norm_qualifier(p) for p in parts[1:]]
    qualifiers = [q for q in qualifiers if q]

    try:
        with _conn() as c:
            rows = c.execute("""
                SELECT DISTINCT p.id,p.name,p.lat,p.lon,p.tz,p.region_ru,p.district,p.alternatenames,
                       coalesce(p.population,0) pop
                FROM geo.place_names n JOIN geo.places p ON p.id=n.id
                WHERE n.name_lower=%s
                ORDER BY pop DESC NULLS LAST LIMIT 2000
            """, (name.strip().lower(),)).fetchall()
    except Exception:
        return {"none": True}

    if not rows:
        return {"none": True}

    # скоринг по квалификаторам (регион / район / alternatenames через транслит):
    # берём кандидатов с максимумом совпадений (если есть хоть одно)
    if qualifiers:
        def _match(q, hay, hay_tr):
            if q in hay or _translit(q) in hay_tr:
                return True
            qt = _translit(q)
            return len(qt) >= 5 and qt[:6] in hay_tr  # префикс: «маслянино» ~ «maslyaninskiy»

        scored = []
        for r in rows:
            hay = " ".join(str(x).lower() for x in (r[5], r[6], r[7]) if x)  # region_ru, district, alt
            hay_tr = _translit(hay)
            score = sum(1 for q in qualifiers if _match(q, hay, hay_tr))
            scored.append((score, r))
        best = max(s for s, _ in scored)
        if best > 0:
            rows = [r for s, r in scored if s == best]

    if len(rows) == 1:
        return {"match": _fmt(rows[0][:9])}
    # несколько — список для уточнения
    cands = []
    for r in rows[:10]:
        f = _fmt(r[:9])
        loc = ", ".join(x for x in (f.get("district"), f.get("region")) if x)
        f["label"] = f"{f['city']}" + (f", {loc}" if loc else "") + f" ({f['lat']:.3f}, {f['lon']:.3f})"
        cands.append(f)
    return {"candidates": cands}
