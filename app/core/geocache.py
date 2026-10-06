"""Кеш геокодинга в PostgreSQL (util.geocode_cache). Fail-safe: при любой ошибке — no-op.

Кешируются результаты внешнего геокодера (Nominatim), чтобы не дёргать его повторно
и обеспечить детерминизм: один запрос → один сохранённый результат.
"""

from __future__ import annotations

import os

_DSN = (os.getenv("DATABASE_URL", "") or "").replace("postgresql+psycopg://", "postgresql://")


def _conn():
    import psycopg
    return psycopg.connect(_DSN, connect_timeout=3)


def ensure_table() -> None:
    if not _DSN:
        return
    try:
        with _conn() as c:
            c.execute("CREATE SCHEMA IF NOT EXISTS util")
            c.execute("""
                CREATE TABLE IF NOT EXISTS util.geocode_cache(
                    query text PRIMARY KEY,
                    city text, lat double precision, lon double precision,
                    tz text, source text, created_at timestamptz DEFAULT now())
            """)
    except Exception:
        pass


def get(query: str) -> dict | None:
    if not _DSN:
        return None
    try:
        with _conn() as c:
            row = c.execute(
                "SELECT city,lat,lon,tz,source FROM util.geocode_cache WHERE query=%s",
                (query.strip().lower(),)).fetchone()
        if row:
            return {"city": row[0], "lat": row[1], "lon": row[2], "tz": row[3],
                    "source": f"cache:{row[4]}"}
    except Exception:
        return None
    return None


def put(query: str, city: str, lat: float, lon: float, tz: str, source: str) -> None:
    if not _DSN:
        return
    try:
        with _conn() as c:
            c.execute("""
                INSERT INTO util.geocode_cache(query,city,lat,lon,tz,source)
                VALUES (%s,%s,%s,%s,%s,%s)
                ON CONFLICT (query) DO NOTHING
            """, (query.strip().lower(), city, lat, lon, tz, source))
    except Exception:
        pass
