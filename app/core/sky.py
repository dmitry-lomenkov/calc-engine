"""«Небо сейчас»: последовательность переходов (накшатра/титхи/йога) + события (Медини).

Всё сидерическое, с той же айанамшей, что и вся панчанга сайта (settings.AYANAMSHA).
Моменты возвращаются в UTC (ISO8601 Z) — браузер переводит в пояс посетителя.
"""
from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone

import swisseph as swe

from . import constants as K
from . import ephe
from . import panchanga as P

LAT = {"Sun": "Su", "Moon": "Mo", "Mars": "Ma", "Mercury": "Me", "Jupiter": "Ju",
       "Venus": "Ve", "Saturn": "Sa", "Rahu": "Ra", "Ketu": "Ke"}
# медленные планеты (для блока «медленные в знаках») и те, у кого бывает ретроградность
SLOW = ("Jupiter", "Saturn", "Rahu", "Ketu")
RETRO_BODIES = ("Mercury", "Venus", "Mars", "Jupiter", "Saturn")
# опорные точки для видимости затмений в России
_RU_POINTS = ((55.75, 37.62), (55.03, 82.92), (43.12, 131.89))  # Москва, Новосибирск, Владивосток


def _utc_iso(jd: float | None) -> str | None:
    if jd is None:
        return None
    y, m, d, ut = swe.revjul(jd, swe.GREG_CAL)
    return (datetime(y, m, d, tzinfo=timezone.utc) + timedelta(hours=ut)).strftime("%Y-%m-%dT%H:%M:%SZ")


def _date_utc(jd: float) -> str:
    return (_utc_iso(jd) or "")[:10]


def _lon(name: str, jd: float) -> float:
    return ephe.graha_positions(jd)[name]["lon"]


def _spd(name: str, jd: float) -> float:
    return ephe.graha_positions(jd)[name]["speed"]


def _sign_idx(name: str, jd: float) -> int:
    return int(_lon(name, jd) // 30) % 12


def _bisect(on_a_side, a: float, b: float, iters: int = 28) -> float:
    for _ in range(iters):
        m = (a + b) / 2
        if on_a_side(m):
            a = m
        else:
            b = m
    return (a + b) / 2


# ── последовательность переходов (накшатра/титхи/йога) ──
def _moon_phase(jd: float) -> dict:
    sun, moon = ephe.sun_moon_lon(jd)
    elong = (moon - sun) % 360.0
    illum = round((1 - math.cos(math.radians(elong))) / 2 * 100, 1)
    return {"illumination_pct": illum, "waxing": elong < 180.0,
            "phase_name": P._moon_phase_name(elong)}


def _segments(jd0: float, hours: float, value_fn, end_fn, fmt) -> list[dict]:
    end_window = jd0 + hours / 24.0
    out, jd, guard = [], jd0, 0
    while jd < end_window and guard < 80:
        guard += 1
        cur = value_fn(jd)
        e = end_fn(jd)
        out.append({**fmt(cur), "end_utc": _utc_iso(e)})
        if e is None:
            break
        jd = e + 2.0 / 1440.0  # +2 мин за границу
    # «следующее» имя = имя следующего сегмента
    for i, seg in enumerate(out):
        seg["next_name"] = out[i + 1]["name"] if i + 1 < len(out) else None
    return out


def sky_sequence(jd0: float, hours: float = 48.0) -> dict:
    nak = _segments(jd0, hours, P.nakshatra_of_moon, P.nakshatra_end,
                    lambda c: {"name": c["name_ru"], "name_en": c["name"]})
    tit = _segments(jd0, hours, P.tithi, P.tithi_end,
                    lambda c: {"name": c["name"], "paksha": c["paksha"],
                               "waxing": c["paksha"] == "Shukla"})
    yog = _segments(jd0, hours, P.yoga, P.yoga_end, lambda c: {"name": c["name"]})
    return {"now_utc": _utc_iso(jd0), "window_hours": hours,
            "nakshatra": nak, "tithi": tit, "yoga": yog, "moon": _moon_phase(jd0)}


# ── события (Медини) ──
def _scan_ingress(name: str, jd0: float, end: float, step: float = 1.0) -> list[dict]:
    ev, prev, prev_sign = [], jd0, _sign_idx(name, jd0)
    while prev < end:
        jd = min(prev + step, end)
        s = _sign_idx(name, jd)
        if s != prev_sign:
            tj = _bisect(lambda m, ps=prev_sign: _sign_idx(name, m) == ps, prev, jd)
            to_idx = _sign_idx(name, tj + 1e-3)
            ev.append({"graha": name, "from_idx": prev_sign, "to_idx": to_idx, "jd": tj})
            prev_sign = to_idx
        if jd >= end:
            break
        prev = jd
    return ev


def _scan_station(name: str, jd0: float, end: float, step: float = 1.0) -> list[dict]:
    ev, prev = [], jd0
    ps = _spd(name, prev)
    while prev < end:
        jd = min(prev + step, end)
        s = _spd(name, jd)
        if (ps < 0) != (s < 0):
            tj = _bisect(lambda m, base=ps: (_spd(name, m) < 0) == (base < 0), prev, jd)
            ev.append({"type": "retro_start" if ps > 0 else "retro_end", "graha": name, "jd": tj})
        if jd >= end:
            break
        prev, ps = jd, s
    return ev


def _moon_alt(jd: float, lat: float, lon: float) -> float:
    xx = swe.calc_ut(jd, swe.MOON, swe.FLG_SWIEPH)[0]
    return swe.azalt(jd, swe.ECL2HOR, (lon, lat, 0.0), 0.0, 0.0, (xx[0], xx[1], xx[2]))[1]


def _eclipse_visible_ru(jd: float, solar: bool) -> bool:
    try:
        for lat, lon in _RU_POINTS:
            if solar:
                attr = swe.sol_eclipse_how(jd, (lon, lat, 0.0), swe.FLG_SWIEPH)
                if attr and attr[0] and attr[0][0] > 0:  # магнитуда в точке > 0
                    return True
            else:
                if _moon_alt(jd, lat, lon) > 0:  # Луна над горизонтом → лунное видно
                    return True
    except Exception:
        return False
    return False


def _eclipses(jd0: float, end: float) -> list[dict]:
    ev = []
    try:
        jd = jd0
        for _ in range(6):
            r = swe.sol_eclipse_when_glob(jd, swe.FLG_SWIEPH, 0, False)
            tmax = r[1][0]
            if tmax >= end:
                break
            if tmax >= jd0:
                ev.append({"type": "eclipse", "sub": "solar", "jd": tmax,
                           "visible_ru": _eclipse_visible_ru(tmax, True)})
            jd = tmax + 2.0
    except Exception:
        pass
    try:
        jd = jd0
        for _ in range(6):
            r = swe.lun_eclipse_when(jd, swe.FLG_SWIEPH, 0, False)
            tmax = r[1][0]
            if tmax >= end:
                break
            if tmax >= jd0:
                ev.append({"type": "eclipse", "sub": "lunar", "jd": tmax,
                           "visible_ru": _eclipse_visible_ru(tmax, False)})
            jd = tmax + 2.0
    except Exception:
        pass
    return ev


def _rashi_ru(idx: int) -> str:
    return K.RASHIS[idx % 12]["ru"]


def sky_events(jd0: float, days: int = 30) -> dict:
    end = jd0 + days
    pos = ephe.graha_positions(jd0)
    # ретроградные СЕЙЧАС (без Раху/Кету — узлы в средних всегда ретро)
    retro_now = [{"graha": n, "latin": LAT[n], "graha_ru": K.GRAHA_RU[n]}
                 for n in RETRO_BODIES if pos[n]["retrograde"]]
    slow = [{"graha": n, "latin": LAT[n], "graha_ru": K.GRAHA_RU[n],
             "rashi_ru": ephe.split_longitude(pos[n]["lon"])["rashi_ru"],
             "rashi_idx": int(pos[n]["lon"] // 30) % 12} for n in SLOW]

    raw = []
    for e in _scan_ingress("Sun", jd0, end):
        raw.append({**e, "type": "sankranti"})
    for name in SLOW:
        for e in _scan_ingress(name, jd0, end):
            raw.append({**e, "type": "ingress"})
    for name in RETRO_BODIES:
        raw += _scan_station(name, jd0, end)
    raw += _eclipses(jd0, end)

    events = []
    for e in raw:
        d = _date_utc(e["jd"])
        t = e["type"]
        out = {"type": t, "date_utc": _utc_iso(e["jd"]), "date": d}
        if t in ("sankranti", "ingress"):
            g = e["graha"]
            out.update({"id": f"{t}_{g}_{d}", "graha": g, "latin": LAT[g], "graha_ru": K.GRAHA_RU[g],
                        "from_rashi_ru": _rashi_ru(e["from_idx"]), "to_rashi_ru": _rashi_ru(e["to_idx"]),
                        "to_idx": e["to_idx"]})
        elif t in ("retro_start", "retro_end"):
            g = e["graha"]
            out.update({"id": f"{t}_{g}_{d}", "graha": g, "latin": LAT[g], "graha_ru": K.GRAHA_RU[g]})
        elif t == "eclipse":
            out.update({"id": f"eclipse_{e['sub']}_{d}", "sub": e["sub"], "visible_ru": e["visible_ru"]})
        events.append(out)
    events.sort(key=lambda x: x["date_utc"])

    return {"now_utc": _utc_iso(jd0), "days": days,
            "retrograde_now": retro_now, "slow_planets": slow, "events": events}
