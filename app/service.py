"""Сервисный слой: связывает геокодинг, время (в т.ч. неизвестное/примерное) и расчёты."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from . import settings
from .core import astro, compat, dasha, ephe, panchanga, personal_day, sky, transits
from .core import constants as K
from .core.geo import geocode, to_utc

_PERIODS = {
    "morning": (6, 12), "day": (12, 18), "evening": (18, 24), "night": (0, 6),
}


def _parse_dt(date: str, time: str | None) -> datetime:
    t = time or "00:00"
    parts = [int(x) for x in t.split(":")]
    while len(parts) < 3:
        parts.append(0)
    y, m, d = [int(x) for x in date.split("-")]
    return datetime(y, m, d, parts[0], parts[1], parts[2])


def _jd_from_local(local_naive: datetime, tz_name: str):
    utc, off, ambiguous = to_utc(local_naive, tz_name)
    jd = ephe.julday(utc.year, utc.month, utc.day,
                     utc.hour + utc.minute / 60 + utc.second / 3600)
    return jd, utc, off, ambiguous


def _moon_segments(loc: dict, day: str, t0: datetime, t1: datetime, step_min: int = 10):
    """Сегменты местного интервала [t0,t1], где накшатра Луны постоянна.
    Возвращает список (seg_start_local, seg_end_local, nak_idx, rashi_idx, rep_jd)."""
    tz = loc["tz"]
    segs = []
    cur = t0
    seg_start = t0
    jd0, _, _, _ = _jd_from_local(t0, tz)
    cur_nak = ephe.split_longitude(ephe.graha_positions(jd0)["Moon"]["lon"])["nakshatra_idx"]
    while cur < t1:
        cur = min(cur + timedelta(minutes=step_min), t1)
        jd, _, _, _ = _jd_from_local(cur, tz)
        nak = ephe.split_longitude(ephe.graha_positions(jd)["Moon"]["lon"])["nakshatra_idx"]
        if nak != cur_nak or cur >= t1:
            mid = seg_start + (cur - seg_start) / 2
            rep_jd, _, _, _ = _jd_from_local(mid, tz)
            rashi = ephe.split_longitude(ephe.graha_positions(rep_jd)["Moon"]["lon"])["rashi_idx"]
            segs.append((seg_start, cur, cur_nak, rashi, rep_jd))
            seg_start = cur
            cur_nak = nak
    return segs


_NAK = 360.0 / 27  # 13°20'


def _boundary_info(lon: float, rate_deg_per_min: float, kind: str, threshold_min: float = 20.0):
    """Близость долготы к границе накшатры/знака и сколько это минут времени рождения."""
    size = _NAK if kind == "nakshatra" else 30.0
    nxt = (int(lon // size) + 1) * size
    prv = int(lon // size) * size
    res = []
    if rate_deg_per_min and abs(rate_deg_per_min) > 1e-9:
        t_next = (nxt - lon) / rate_deg_per_min
        t_prev = (lon - prv) / rate_deg_per_min
        if 0 < t_next <= threshold_min:
            res.append({"kind": kind, "direction": "next", "minutes": round(t_next, 1),
                        "note": f"через ~{round(t_next)} мин перейдёт в следующий(ую) {kind}"})
        if 0 < t_prev <= threshold_min:
            res.append({"kind": kind, "direction": "prev", "minutes": round(t_prev, 1),
                        "note": f"при рождении на ~{round(t_prev)} мин раньше был(а) предыдущий(ая) {kind}"})
    return res


def _near_boundary(jd: float, lat: float, lon: float, grahas: list[dict]) -> list[dict]:
    flags = []
    d = 1.0 / 1440.0  # 1 минута
    # скорость асцендента (°/мин)
    a0 = ephe.ascendant(jd, lat, lon)
    a1 = ephe.ascendant(jd + d, lat, lon)
    rate_asc = ((a1 - a0 + 540) % 360 - 180)
    for b in _boundary_info(a0, rate_asc, "nakshatra") + _boundary_info(a0, rate_asc, "sign"):
        flags.append({"body": "lagna", **b})
    # Луна (°/мин из суточной скорости)
    moon = next(g for g in grahas if g["graha"] == "Moon")
    rate_moon = moon["speed"] / 1440.0
    for b in _boundary_info(moon["longitude"], rate_moon, "nakshatra") + _boundary_info(moon["longitude"], rate_moon, "sign"):
        flags.append({"body": "moon", **b})
    return flags


def _chart_at(jd: float, utc: datetime, lagna: dict | None, dasha_levels: int) -> dict:
    lagna_idx = lagna["rashi_idx"] if lagna else None
    grahas = astro.natal_grahas(jd, lagna_idx)
    moon = next(g for g in grahas if g["graha"] == "Moon")
    navamsa_lagna_idx = lagna["navamsa_rashi_idx"] if lagna and "navamsa_rashi_idx" in lagna else None
    vim = dasha.vimshottari(moon["longitude"], utc, levels=dasha_levels)
    return {
        "grahas_d1": grahas,
        "d9": astro.d9_chart(grahas, navamsa_lagna_idx),
        "chandra_lagna": astro.moon_chandra_lagna(grahas),
        "vimshottari_dasha": vim,
    }


def compute_natal(inp) -> dict:
    loc = geocode(inp.place, inp.lat, inp.lon, inp.tz_name, getattr(inp, "geoname_id", None))
    meta_loc = {"city": loc["city"], "lat": loc["lat"], "lon": loc["lon"],
                "tz": loc["tz"], "source": loc["source"],
                "confirm": f"{loc['city']}, {loc['tz']} — верно?"}

    base = {
        "engine_version": settings.ENGINE_VERSION,
        "settings": settings.SETTINGS_DICT,
        "input": inp.model_dump(),
        "resolved_location": meta_loc,
    }

    # ── Точное время ──
    if inp.time_precision == "exact":
        local = _parse_dt(inp.date, inp.time)
        jd, utc, off, ambiguous = _jd_from_local(local, loc["tz"])
        lagna = astro.natal_lagna(jd, loc["lat"], loc["lon"])
        # для навамса-лагны нужен индекс навамсы асцендента
        lagna["navamsa_rashi_idx"] = ephe.split_longitude(lagna["longitude"])["navamsa_rashi_idx"]
        chart = _chart_at(jd, utc, lagna, inp.dasha_levels)
        near = _near_boundary(jd, loc["lat"], loc["lon"], chart["grahas_d1"])
        base.update({
            "time_unknown": False,
            "utc": utc.strftime("%Y-%m-%d %H:%M:%S"),
            "utc_offset_hours": off,
            "dst_ambiguous": ambiguous,
            "lagna": lagna,
            "near_boundary": near,
            **chart,
        })
        # Тропический (западный) знак Солнца: сид. долгота + аянамша (аддитивно, не ломает ответ)
        _sun = next((g for g in chart["grahas_d1"] if g["graha"] == "Sun"), None)
        if _sun is not None:
            _ayan = ephe.ayanamsha_value(jd)
            _trop = (_sun["longitude"] + _ayan) % 360.0
            _ti = int(_trop // 30)
            base["ayanamsha"] = round(_ayan, 6)
            base["sun_tropical"] = {
                "rashi_idx": _ti,
                "rashi_en": K.RASHIS[_ti]["en"],
                "rashi_ru": K.RASHIS[_ti]["ru"],
                "longitude": round(_trop, 6),
            }
        if ambiguous:
            base.setdefault("notes", []).append(
                "время попало в неоднозначный час перевода стрелок; взят fold=0")
        return base

    # ── Неизвестное / примерное время → диапазон + карта от Луны ──
    if inp.time_precision == "approximate":
        h0, h1 = _PERIODS[inp.approximate_period]
        t0 = _parse_dt(inp.date, f"{h0:02d}:00")
        t1 = _parse_dt(inp.date, "23:59:59") if h1 == 24 else _parse_dt(inp.date, f"{h1:02d}:00")
        window = f"{inp.approximate_period} ({h0:02d}:00–{h1 if h1<24 else 24:02d}:00)"
    else:
        t0 = _parse_dt(inp.date, "00:00")
        t1 = _parse_dt(inp.date, "23:59:59")
        window = "весь день (время неизвестно)"

    segs = _moon_segments(loc, inp.date, t0, t1)
    variants = []
    for (s0, s1, nak_idx, rashi_idx, rep_jd) in segs:
        _, rep_utc, off, _ = _jd_from_local(s0 + (s1 - s0) / 2, loc["tz"])
        chart = _chart_at(rep_jd, rep_utc, None, inp.dasha_levels)
        chart["vimshottari_dasha"]["reliability"] = "приблизительно (время неизвестно)"
        variants.append({
            "interval_local": f"{s0.strftime('%H:%M')}–{s1.strftime('%H:%M')}",
            "moon_nakshatra": K.NAKSHATRAS[nak_idx]["en"],
            "moon_nakshatra_ru": K.NAKSHATRAS[nak_idx]["ru"],
            "moon_rashi": K.RASHIS[rashi_idx]["en"],
            "moon_rashi_ru": K.RASHIS[rashi_idx]["ru"],
            "utc_offset_hours": off,
            **chart,
        })

    notes = [
        "Время рождения неизвестно/примерно: лагна и дома НЕ рассчитаны.",
        "Основа карты — Чандра-лагна (от Луны).",
        "Даши даны с пометкой о неточности.",
    ]
    if len(variants) > 1:
        notes.append(
            f"В этот день Луна меняет накшатру/знак — возвращено {len(variants)} варианта "
            "с интервалами времени (уточните время рождения для выбора).")
    else:
        notes.append("Луна весь интервал в одной накшатре — вариант единственный.")

    base.update({
        "time_unknown": True,
        "time_window": window,
        "lagna": None,
        "variants": variants,
        "notes": notes,
    })
    return base


def compute_panchanga(inp) -> dict:
    loc = geocode(inp.place, inp.lat, inp.lon, inp.tz_name, getattr(inp, "geoname_id", None))
    local = _parse_dt(inp.date, inp.time)
    jd, utc, off, _ = _jd_from_local(local, loc["tz"])
    p = panchanga.full_panchanga(jd, loc["lat"], loc["lon"], off, local,
                                 at_sunrise=getattr(inp, "at_sunrise", False))
    return {
        "engine_version": settings.ENGINE_VERSION,
        "settings": settings.SETTINGS_DICT,
        "resolved_location": {"city": loc["city"], "lat": loc["lat"], "lon": loc["lon"],
                              "tz": loc["tz"], "confirm": f"{loc['city']}, {loc['tz']} — верно?"},
        "date": inp.date, "utc": utc.strftime("%Y-%m-%d %H:%M:%S"), "utc_offset_hours": off,
        "panchanga": p,
    }


def _jd_utc_now_or(datetime_utc: str | None) -> float:
    """jd(UT) из переданного UTC-времени или из текущего серверного UTC."""
    if datetime_utc:
        d, t = (datetime_utc.split(" ") + ["00:00"])[:2] if " " in datetime_utc else (datetime_utc, "00:00")
        dt = _parse_dt(d, t)
    else:
        dt = datetime.now(timezone.utc)
    return ephe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60 + dt.second / 3600)


def compute_sky_sequence(inp) -> dict:
    jd = _jd_utc_now_or(getattr(inp, "datetime_utc", None))
    return {"engine_version": settings.ENGINE_VERSION, "settings": settings.SETTINGS_DICT,
            **sky.sky_sequence(jd, getattr(inp, "hours", 48.0) or 48.0)}


def compute_sky_events(inp) -> dict:
    jd = _jd_utc_now_or(getattr(inp, "datetime_utc", None))
    return {"engine_version": settings.ENGINE_VERSION, "settings": settings.SETTINGS_DICT,
            **sky.sky_events(jd, getattr(inp, "days", 30) or 30)}


def compute_transits(inp) -> dict:
    dt = _parse_dt(inp.datetime_utc.split(" ")[0], inp.datetime_utc.split(" ")[1]
                   if " " in inp.datetime_utc else "00:00")
    jd = ephe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute / 60 + dt.second / 3600)
    return {
        "engine_version": settings.ENGINE_VERSION,
        "settings": settings.SETTINGS_DICT,
        "datetime_utc": dt.strftime("%Y-%m-%d %H:%M:%S"),
        "transits": transits.transits(jd),
    }


def _moon_rashi_nak(inp) -> tuple[int, int]:
    loc = geocode(inp.place, inp.lat, inp.lon, inp.tz_name, getattr(inp, "geoname_id", None))
    # для совместимости достаточно Луны; при неизвестном времени берём полдень
    local = _parse_dt(inp.date, inp.time or "12:00")
    jd, _, _, _ = _jd_from_local(local, loc["tz"])
    s = ephe.split_longitude(ephe.graha_positions(jd)["Moon"]["lon"])
    return s["rashi_idx"], s["nakshatra_idx"]


def compute_personal_day(inp) -> dict:
    b = inp.birth
    loc = geocode(b.place, b.lat, b.lon, b.tz_name, getattr(b, "geoname_id", None))
    # натальная Луна (при неизвестном времени — полдень)
    blocal = _parse_dt(b.date, b.time or "12:00")
    bjd, _, _, _ = _jd_from_local(blocal, loc["tz"])
    natal_moon = ephe.graha_positions(bjd)["Moon"]["lon"]
    # Луна дня — на 06:00 местного времени места рождения
    dlocal = _parse_dt(inp.day, "06:00")
    djd, _, _, _ = _jd_from_local(dlocal, loc["tz"])
    pd = personal_day.personal_day(natal_moon, djd)
    return {
        "engine_version": settings.ENGINE_VERSION,
        "settings": settings.SETTINGS_DICT,
        "resolved_location": {"city": loc["city"], "tz": loc["tz"]},
        "day": inp.day,
        "personal_day": pd,
    }


def compute_compatibility(inp) -> dict:
    a_rashi, a_nak = _moon_rashi_nak(inp.person_a)
    b_rashi, b_nak = _moon_rashi_nak(inp.person_b)
    result = compat.ashtakuta(a_rashi, a_nak, b_rashi, b_nak)
    return {
        "engine_version": settings.ENGINE_VERSION,
        "settings": settings.SETTINGS_DICT,
        "person_a": {"moon_rashi": K.RASHIS[a_rashi]["en"], "moon_nakshatra": K.NAKSHATRAS[a_nak]["en"]},
        "person_b": {"moon_rashi": K.RASHIS[b_rashi]["en"], "moon_nakshatra": K.NAKSHATRAS[b_nak]["en"]},
        "ashtakuta": result,
    }
