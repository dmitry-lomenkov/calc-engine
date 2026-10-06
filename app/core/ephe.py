"""Обвязка Swiss Ephemeris: инициализация, сидерический режим, базовые расчёты граха."""

from __future__ import annotations

import threading

import swisseph as swe

from .. import settings
from . import constants as K

_lock = threading.Lock()
_initialized = False

_SID_MODE = {
    "lahiri": swe.SIDM_LAHIRI,
    "raman": swe.SIDM_RAMAN,
    "krishnamurti": swe.SIDM_KRISHNAMURTI,
}

# soft-body id для swisseph
_SWE_ID = {
    "Sun": swe.SUN, "Moon": swe.MOON, "Mars": swe.MARS, "Mercury": swe.MERCURY,
    "Jupiter": swe.JUPITER, "Venus": swe.VENUS, "Saturn": swe.SATURN,
}


def init() -> None:
    global _initialized
    with _lock:
        if _initialized:
            return
        swe.set_ephe_path(settings.EPHE_PATH)
        swe.set_sid_mode(_SID_MODE.get(settings.AYANAMSHA, swe.SIDM_LAHIRI), 0, 0)
        _initialized = True


def julday(y: int, m: int, d: int, ut_hour: float) -> float:
    """Юлианский день UT из компонентов UTC."""
    init()
    return swe.julday(y, m, d, ut_hour, swe.GREG_CAL)


def _calc(jd: float, body: int) -> tuple[float, float]:
    """Сидерическая долгота и скорость по долготе (град/день)."""
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL | swe.FLG_SPEED
    res = swe.calc_ut(jd, body, flags)
    xx = res[0]
    return xx[0] % 360.0, xx[3]


def graha_positions(jd: float) -> dict[str, dict]:
    """Позиции 9 граха: сидерическая долгота, скорость, ретроградность."""
    init()
    out: dict[str, dict] = {}
    for name in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn"):
        lon, spd = _calc(jd, _SWE_ID[name])
        out[name] = {"lon": lon, "speed": spd, "retrograde": spd < 0}
    # Раху/Кету
    node_body = swe.TRUE_NODE if settings.NODE_TYPE == "true" else swe.MEAN_NODE
    rahu_lon, rahu_spd = _calc(jd, node_body)
    out["Rahu"] = {"lon": rahu_lon, "speed": rahu_spd, "retrograde": True}  # узлы всегда ретро
    out["Ketu"] = {"lon": (rahu_lon + 180.0) % 360.0, "speed": rahu_spd, "retrograde": True}
    return out


def sun_moon_lon(jd: float) -> tuple[float, float]:
    """Быстро: только сидерические долготы Солнца и Луны (для поиска окончаний титхи/накшатры)."""
    init()
    flags = swe.FLG_SWIEPH | swe.FLG_SIDEREAL
    sun = swe.calc_ut(jd, swe.SUN, flags)[0][0] % 360.0
    moon = swe.calc_ut(jd, swe.MOON, flags)[0][0] % 360.0
    return sun, moon


def sun_altitude(jd: float, lat: float, lon: float) -> float:
    """Видимая высота центра Солнца над горизонтом (град) — для полярного дня/ночи."""
    init()
    # тропическая эклиптич. долгота/широта Солнца
    xx = swe.calc_ut(jd, swe.SUN, swe.FLG_SWIEPH)[0]
    az = swe.azalt(jd, swe.ECL2HOR, (lon, lat, 0.0), 0.0, 0.0, (xx[0], xx[1], xx[2]))
    return az[1]  # true altitude


def ascendant(jd: float, lat: float, lon: float) -> float:
    """Сидерический асцендент (лагна), градусы 0..360. Дома — Whole Sign отдельно."""
    init()
    # 'W' = Whole sign в swisseph; ascmc[0] = Ascendant. FLG_SIDEREAL → сидерические значения.
    cusps, ascmc = swe.houses_ex(jd, lat, lon, b"W", swe.FLG_SIDEREAL)
    return ascmc[0] % 360.0


def ayanamsha_value(jd: float) -> float:
    init()
    return swe.get_ayanamsa_ut(jd)


# ── Разбор долготы на раши / накшатру / паду ──
def split_longitude(lon: float) -> dict:
    lon = lon % 360.0
    rashi_idx = int(lon // 30)
    deg_in_sign = lon - rashi_idx * 30
    arcmin = lon * 60.0
    nak_idx = int(arcmin // 800) % 27           # 13°20' = 800'
    pos_in_nak = arcmin - nak_idx * 800
    pada = int(pos_in_nak // 200) + 1           # 4 пады по 3°20' = 200'
    # навамса (D9): floor(lon / 3°20') mod 12
    navamsa_idx = int(arcmin // 200) % 12
    return {
        "lon": round(lon, 6),
        "rashi_idx": rashi_idx,
        "rashi_en": K.RASHIS[rashi_idx]["en"],
        "rashi_ru": K.RASHIS[rashi_idx]["ru"],
        "deg_in_sign": round(deg_in_sign, 6),
        "nakshatra_idx": nak_idx,
        "nakshatra_en": K.NAKSHATRAS[nak_idx]["en"],
        "nakshatra_ru": K.NAKSHATRAS[nak_idx]["ru"],
        "pada": pada,
        "navamsa_rashi_idx": navamsa_idx,
        "navamsa_rashi_en": K.RASHIS[navamsa_idx]["en"],
    }


def deg_to_dms(deg: float) -> str:
    """Градусы в знаке → строка Д°ММ'СС""."""
    d = int(deg)
    mfloat = (deg - d) * 60
    m = int(mfloat)
    s = int(round((mfloat - m) * 60))
    if s == 60:
        s = 0
        m += 1
    if m == 60:
        m = 0
        d += 1
    return f"{d}°{m:02d}'{s:02d}\""
