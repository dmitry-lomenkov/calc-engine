"""JYOTISHA 365 — calc_engine (изолированный сервис ведических расчётов).

ВАЖНО (лицензия): использует Swiss Ephemeris (pyswisseph) под AGPL-3.0 → отдельный сервис
с собственным LICENSE (см. calc_engine/LICENSE, NOTICE), готовый к публикации исходников.

Все эндпоинты версионированы (/v1/...), вход/выход — строгие JSON-схемы (pydantic).
Ответ детерминирован для одних и тех же входных данных и содержит engine_version + settings.
Часовые пояса (в т.ч. историческое декретное/летнее время СССР) берутся из IANA (zoneinfo).
"""

from __future__ import annotations

from fastapi import FastAPI, HTTPException

from . import settings
from fastapi.responses import JSONResponse

from .core.geo import GeoError, GeoAmbiguous
from . import schemas, service

app = FastAPI(title="JYOTISHA 365 · calc_engine", version=settings.ENGINE_VERSION)


@app.on_event("startup")
def _startup() -> None:
    from .core import geocache
    geocache.ensure_table()  # fail-safe: no-op без DATABASE_URL


def _guard(fn, *a):
    try:
        return fn(*a)
    except GeoAmbiguous as e:
        # не ошибка: несколько совпадений — просим уточнить выбор (geoname_id)
        return JSONResponse(status_code=200, content={
            "need_disambiguation": True,
            "message": "Найдено несколько мест — уточните, передав geoname_id выбранного варианта.",
            "candidates": e.candidates,
        })
    except GeoError as e:
        raise HTTPException(status_code=422, detail=f"geo: {e}")
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")


@app.get("/health")
def health() -> dict:
    try:
        import swisseph as swe
        swe_ok = {"available": True, "version": swe.version}
    except Exception as e:  # noqa: BLE001
        swe_ok = {"available": False, "error": str(e)}
    return {"ok": True, "service": "calc_engine", "engine_version": settings.ENGINE_VERSION,
            "settings": settings.SETTINGS_DICT, "swisseph": swe_ok}


@app.post("/v1/natal")
def natal(inp: schemas.BirthInput) -> dict:
    return _guard(service.compute_natal, inp)


@app.post("/v1/dasha")
def dasha_ep(inp: schemas.BirthInput) -> dict:
    full = _guard(service.compute_natal, inp)
    # компактный ответ по дашам
    out = {k: full[k] for k in ("engine_version", "settings", "resolved_location") if k in full}
    out["time_unknown"] = full.get("time_unknown")
    if full.get("time_unknown"):
        out["variants"] = [{"interval_local": v["interval_local"],
                            "vimshottari_dasha": v["vimshottari_dasha"]} for v in full["variants"]]
    else:
        out["vimshottari_dasha"] = full["vimshottari_dasha"]
    return out


@app.post("/v1/panchanga")
def panchanga_ep(inp: schemas.PanchangaInput) -> dict:
    return _guard(service.compute_panchanga, inp)


@app.post("/v1/transits")
def transits_ep(inp: schemas.TransitInput) -> dict:
    return _guard(service.compute_transits, inp)


@app.post("/v1/compatibility")
def compatibility_ep(inp: schemas.CompatInput) -> dict:
    return _guard(service.compute_compatibility, inp)


@app.post("/v1/personal_day")
def personal_day_ep(inp: schemas.PersonalDayInput) -> dict:
    return _guard(service.compute_personal_day, inp)


@app.post("/v1/sky_sequence")
def sky_sequence_ep(inp: schemas.SkySequenceInput) -> dict:
    return _guard(service.compute_sky_sequence, inp)


@app.post("/v1/sky_events")
def sky_events_ep(inp: schemas.SkyEventsInput) -> dict:
    return _guard(service.compute_sky_events, inp)


@app.post("/v1/nearest_place")
def nearest_place_ep(inp: schemas.GeocodeInput) -> dict:
    """Самое населённое место GeoNames рядом с координатами (базовый размер звезды по населению)."""
    if inp.lat is None or inp.lon is None:
        raise HTTPException(status_code=422, detail="нужны lat и lon")
    from .core import geonames
    m = geonames.nearest(float(inp.lat), float(inp.lon))
    return {"status": "match", "match": m} if m else {"status": "none"}


@app.post("/v1/geocode")
def geocode_ep(inp: schemas.GeocodeInput) -> dict:
    """Разрешить место (для поиска города на сайте). Не бросает 422 на «не найдено»:
    возвращает status = match | candidates | none. candidates — для уточнения (geoname_id)."""
    from .core.geo import geocode
    try:
        m = geocode(inp.place, inp.lat, inp.lon, inp.tz_name, inp.geoname_id)
        return {"status": "match", "match": m}
    except GeoAmbiguous as e:
        return {"status": "candidates", "candidates": e.candidates}
    except GeoError:
        return {"status": "none"}
    except Exception as e:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {e}")
