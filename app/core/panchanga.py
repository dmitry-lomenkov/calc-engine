"""Панчанга: титхи, накшатра, йога, карана, вара, восход/заход.

Восход/заход считаются по правилу drikpanchang: ВЕРХНИЙ край диска Солнца + атмосферная
рефракция (в swisseph это rise_trans без BIT_DISC_CENTER и без BIT_NO_REFRACTION).
Полярный день/ночь: когда восход/заход отсутствует — возвращаем флаг polar и продолжаем
считать титхи/накшатру/йогу/карану (они зависят только от долгот Солнца/Луны, не от восхода).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import swisseph as swe

from . import constants as K
from . import ephe


def _sun_moon(jd: float) -> tuple[float, float]:
    return ephe.sun_moon_lon(jd)


# ── Текущие лимбы панчанги в момент jd ──
def tithi(jd: float) -> dict:
    sun, moon = _sun_moon(jd)
    diff = (moon - sun) % 360.0
    idx = int(diff // 12)
    paksha = "Shukla" if idx < 15 else "Krishna"
    within = idx % 15
    name = ("Пурнима" if paksha == "Shukla" else "Амавасья") if within == 14 else K.TITHI_NAMES[within]
    return {"index": idx + 1, "name": name, "paksha": paksha}


def yoga(jd: float) -> dict:
    sun, moon = _sun_moon(jd)
    idx = int(((sun + moon) % 360.0) // (360.0 / 27))
    return {"index": idx + 1, "name": K.YOGA_NAMES[idx]}


def karana(jd: float) -> dict:
    sun, moon = _sun_moon(jd)
    half = int(((moon - sun) % 360.0) // 6)
    if half == 0:
        name = K.KARANA_NAMES_FIXED[3]
    elif 1 <= half <= 56:
        name = K.KARANA_NAMES_MOVABLE[(half - 1) % 7]
    else:
        name = K.KARANA_NAMES_FIXED[half - 57]
    return {"index": half + 1, "name": name}


def nakshatra_of_moon(jd: float) -> dict:
    _, moon = _sun_moon(jd)
    s = ephe.split_longitude(moon)
    return {"index": s["nakshatra_idx"] + 1, "name": s["nakshatra_en"],
            "name_ru": s["nakshatra_ru"], "pada": s["pada"]}


# ── Поиск момента окончания (титхи/накшатра) ──
def _find_crossing(jd0: float, value_fn, boundary_step: float, max_days: float = 1.6) -> float | None:
    """Момент, когда монотонно растущая величина value_fn достигает следующей границы,
    кратной boundary_step. Грубый шаг 5 мин + линейное уточнение. Возврат jd (UT)."""
    v0 = value_fn(jd0)
    target = (int(v0 // boundary_step) + 1) * boundary_step
    step = 5.0 / 1440.0  # 5 минут
    prev_jd, prev_v = jd0, v0
    jd = jd0
    n = int(max_days / step)
    for _ in range(n):
        jd += step
        v = value_fn(jd)
        # разворот при переходе 360→0
        if v < prev_v - 1e-6:
            v += 360.0
        if v >= target:
            # линейная интерполяция между prev и текущим
            frac = (target - prev_v) / (v - prev_v) if v != prev_v else 0.0
            return prev_jd + frac * step
        prev_jd, prev_v = jd, v
    return None


def _elong(jd: float) -> float:
    sun, moon = _sun_moon(jd)
    return (moon - sun) % 360.0


def _moon_lon(jd: float) -> float:
    return _sun_moon(jd)[1]


def _sum_lon(jd: float) -> float:
    sun, moon = _sun_moon(jd)
    return (sun + moon) % 360.0


def tithi_end(jd: float) -> float | None:
    return _find_crossing(jd, _elong, 12.0)


def nakshatra_end(jd: float) -> float | None:
    return _find_crossing(jd, _moon_lon, 360.0 / 27)


def yoga_end(jd: float) -> float | None:
    return _find_crossing(jd, _sum_lon, 360.0 / 27)


# ── Восход/заход по правилу drikpanchang ──
def _rise_or_set(jd_start: float, lat: float, lon: float, which: int, body: int = swe.SUN) -> float | None:
    # без BIT_DISC_CENTER → верхний край диска; рефракция включена по умолчанию
    try:
        res = swe.rise_trans(jd_start, body, which, (lon, lat, 0.0), 0.0, 0.0, swe.FLG_SWIEPH)
        ret, tret = res[0], res[1]
        if ret < 0:
            return None
        return tret[0]
    except Exception:
        return None


def _jd_to_local(jd: float, tz_off: float) -> str | None:
    if jd is None:
        return None
    y, m, d, ut = swe.revjul(jd, swe.GREG_CAL)
    dt = datetime(y, m, d, tzinfo=timezone.utc) + timedelta(hours=ut + tz_off)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def sunrise_sunset(local_date: datetime, lat: float, lon: float, tz_off: float) -> dict:
    """Восход и заход ИМЕННО местного календарного дня local_date (00:00 местного)."""
    # jd для местной полуночи (в UT)
    midnight_utc = local_date.replace(hour=0, minute=0, second=0) - timedelta(hours=tz_off)
    jd_mid = ephe.julday(midnight_utc.year, midnight_utc.month, midnight_utc.day,
                         midnight_utc.hour + midnight_utc.minute / 60 + midnight_utc.second / 3600)
    sr = _rise_or_set(jd_mid, lat, lon, swe.CALC_RISE)
    ss = _rise_or_set(sr if sr else jd_mid, lat, lon, swe.CALC_SET)

    polar = sr is None or ss is None
    ptype = None
    if polar:
        alt_noon = ephe.sun_altitude(jd_mid + 0.5, lat, lon)
        ptype = "day" if alt_noon > 0 else "night"
    return {
        "sunrise_local": _jd_to_local(sr, tz_off),
        "sunset_local": _jd_to_local(ss, tz_off),
        "sunrise_jd": round(sr, 8) if sr else None,
        "sunset_jd": round(ss, 8) if ss else None,
        "polar": polar,
        "polar_type": ptype,
    }


def _polar_fallback(local_date: datetime, lat: float, lon: float, tz_off: float) -> dict | None:
    """Полярный день/ночь: восхода нет. Берём восход/заход на БЛИЖАЙШЕЙ широте к экватору
    (тот же меридиан), где восход есть. Возвращает ss-словарь + lat_used."""
    step = -0.5 if lat > 0 else 0.5
    for i in range(1, 40):                     # до ~19.5° к экватору
        la = lat + step * i
        if abs(la) < 1.0:
            break
        r = sunrise_sunset(local_date, la, lon, tz_off)
        if not r["polar"] and r.get("sunrise_jd") and r.get("sunset_jd"):
            r["lat_used"] = round(la, 2)
            return r
    return None


def _moon_phase_name(elong: float) -> str:
    """Русское имя фазы по элонгации Луна−Солнце (0=новолуние, 180=полнолуние)."""
    e = elong % 360.0
    if e < 11.25 or e >= 348.75:
        return "Новолуние"
    if e < 84.375:
        return "Растущий серп"
    if e < 95.625:
        return "Первая четверть"
    if e < 168.75:
        return "Растущая Луна (горбатая)"
    if e < 191.25:
        return "Полнолуние"
    if e < 264.375:
        return "Убывающая Луна (горбатая)"
    if e < 275.625:
        return "Последняя четверть"
    return "Убывающий серп"


def moon_info(jd: float, lat: float, lon: float, tz_off: float, local_dt: datetime) -> dict:
    """Фаза Луны (угол элонгации, % освещённости, растущая/убывающая, имя фазы) +
    восход/заход Луны местного календарного дня. Всё — из swisseph."""
    import math
    sun, moon = _sun_moon(jd)
    elong = (moon - sun) % 360.0
    illum = round((1 - math.cos(math.radians(elong))) / 2 * 100, 1)
    waxing = elong < 180.0
    midnight_utc = local_dt.replace(hour=0, minute=0, second=0) - timedelta(hours=tz_off)
    jd_mid = ephe.julday(midnight_utc.year, midnight_utc.month, midnight_utc.day,
                         midnight_utc.hour + midnight_utc.minute / 60 + midnight_utc.second / 3600)
    mr = _rise_or_set(jd_mid, lat, lon, swe.CALC_RISE, swe.MOON)
    ms = _rise_or_set(mr if mr else jd_mid, lat, lon, swe.CALC_SET, swe.MOON)
    return {
        "phase_angle": round(elong, 1),
        "illumination_pct": illum,
        "waxing": waxing,
        "phase_name": _moon_phase_name(elong),
        "moonrise_local": _jd_to_local(mr, tz_off),
        "moonset_local": _jd_to_local(ms, tz_off),
    }


def vara(local_dt: datetime, sunrise_jd: float | None, birth_jd: float | None, polar: bool) -> dict:
    """Вара начинается с восхода. До восхода — вара предыдущего дня.
    В полярный день/ночь восхода нет → используем гражданский день (флаг)."""
    wd = local_dt.weekday()
    note = None
    if polar:
        note = "полярный день/ночь: восход отсутствует, вара по гражданскому дню"
    elif sunrise_jd is not None and birth_jd is not None and birth_jd < sunrise_jd:
        wd = (wd - 1) % 7
        note = "рождение до восхода — вара предыдущего дня"
    return {"index": wd, "name": K.VARA_NAMES[wd], "note": note}


_EPS = 1.0 / 1440.0  # 1 минута в jd — заглянуть за границу, чтобы узнать следующий элемент


def _with_transitions(jd: float, tz_off: float) -> tuple[dict, dict, dict]:
    """Титхи/накшатра/йога в момент jd + время окончания + КАКОЙ следует за ним
    (drikpanchang показывает «X до HH:MM, затем Y»)."""
    t = tithi(jd)
    te = tithi_end(jd)
    t["end_local"] = _jd_to_local(te, tz_off)
    if te:
        t["next_name"] = tithi(te + _EPS)["name"]

    n = nakshatra_of_moon(jd)
    ne = nakshatra_end(jd)
    n["end_local"] = _jd_to_local(ne, tz_off)
    if ne:
        nn = nakshatra_of_moon(ne + _EPS)
        n["next_name"] = nn["name"]
        n["next_name_ru"] = nn["name_ru"]

    y = yoga(jd)
    ye = yoga_end(jd)
    y["end_local"] = _jd_to_local(ye, tz_off)
    if ye:
        y["next_name"] = yoga(ye + _EPS)["name"]
    return t, n, y


def full_panchanga(jd: float, lat: float, lon: float, tz_off: float, local_dt: datetime,
                   at_sunrise: bool = False) -> dict:
    """at_sunrise=True — титхи/накшатра/йога/карана считаются на МОМЕНТ ВОСХОДА этого дня
    (правило drikpanchang «панчанга дня»); иначе — на переданное время jd."""
    ss = sunrise_sunset(local_dt, lat, lon, tz_off)
    eval_jd = jd
    if at_sunrise and not ss["polar"] and ss.get("sunrise_jd"):
        eval_jd = ss["sunrise_jd"]
    t, n, y = _with_transitions(eval_jd, tz_off)
    out = {
        "tithi": t,
        "nakshatra": n,
        "yoga": y,
        "karana": karana(eval_jd),
        # вара «на восходе» — день восхода (birth_jd == sunrise_jd, сдвига «до восхода» нет)
        "vara": vara(local_dt, ss.get("sunrise_jd"), eval_jd, ss["polar"]),
        "moon": moon_info(eval_jd, lat, lon, tz_off, local_dt),
        "evaluated_at": "sunrise" if (at_sunrise and not ss["polar"]) else "given_time",
        **ss,
    }
    if ss["polar"]:
        fb = _polar_fallback(local_dt, lat, lon, tz_off)
        if fb:
            # показываем восход/заход/мухурты ближайшей широты, где восход есть
            out["sunrise_local"] = fb["sunrise_local"]
            out["sunset_local"] = fb["sunset_local"]
            out["sunrise_jd"] = fb["sunrise_jd"]
            out["sunset_jd"] = fb["sunset_jd"]
            out["polar_fallback_lat"] = fb["lat_used"]
            out["notes"] = [f"Полярн{'ый день' if ss['polar_type']=='day' else 'ая ночь'}: обычного восхода "
                            f"нет — восход и мухурты показаны для ближайшей широты ~{abs(round(fb['lat_used']))}°, "
                            "где восход есть."]
        else:
            out["notes"] = [f"Полярный {'день' if ss['polar_type']=='day' else 'ночь'}: "
                            "восход/заход отсутствуют; титхи/накшатра/йога/карана рассчитаны по долготам."]
    return out
