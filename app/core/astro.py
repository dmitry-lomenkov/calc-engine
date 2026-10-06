"""Сборка натальной карты: грахи D1/D9, лагна, дома Whole Sign, ретроградность."""

from __future__ import annotations

from . import constants as K
from . import ephe


def _house_whole_sign(planet_rashi_idx: int, lagna_rashi_idx: int | None) -> int | None:
    """Номер дома (1..12) по Whole Sign. None, если лагна неизвестна."""
    if lagna_rashi_idx is None:
        return None
    return (planet_rashi_idx - lagna_rashi_idx) % 12 + 1


def natal_grahas(jd: float, lagna_rashi_idx: int | None) -> list[dict]:
    pos = ephe.graha_positions(jd)
    out = []
    for name in ("Sun", "Moon", "Mars", "Mercury", "Jupiter", "Venus", "Saturn", "Rahu", "Ketu"):
        p = pos[name]
        s = ephe.split_longitude(p["lon"])
        out.append({
            "graha": name,
            "graha_ru": K.GRAHA_RU[name],
            "longitude": s["lon"],
            "longitude_dms": ephe.deg_to_dms(s["deg_in_sign"]),
            "rashi": s["rashi_en"],
            "rashi_ru": s["rashi_ru"],
            "rashi_idx": s["rashi_idx"],
            "nakshatra": s["nakshatra_en"],
            "nakshatra_ru": s["nakshatra_ru"],
            "nakshatra_idx": s["nakshatra_idx"],
            "pada": s["pada"],
            "navamsa_rashi": s["navamsa_rashi_en"],
            "navamsa_rashi_idx": s["navamsa_rashi_idx"],
            "retrograde": bool(p["retrograde"]),
            "speed": round(p["speed"], 6),
            "house": _house_whole_sign(s["rashi_idx"], lagna_rashi_idx),
        })
    return out


def natal_lagna(jd: float, lat: float, lon: float) -> dict:
    asc = ephe.ascendant(jd, lat, lon)
    s = ephe.split_longitude(asc)
    return {
        "longitude": s["lon"],
        "longitude_dms": ephe.deg_to_dms(s["deg_in_sign"]),
        "rashi": s["rashi_en"],
        "rashi_ru": s["rashi_ru"],
        "rashi_idx": s["rashi_idx"],
        "nakshatra": s["nakshatra_en"],
        "nakshatra_ru": s["nakshatra_ru"],
        "pada": s["pada"],
        "navamsa_rashi": s["navamsa_rashi_en"],
    }


def moon_chandra_lagna(grahas: list[dict]) -> dict:
    """Чандра-лагна: раши Луны как 1-й дом (когда время рождения неизвестно)."""
    moon = next(g for g in grahas if g["graha"] == "Moon")
    return {"rashi": moon["rashi"], "rashi_ru": moon["rashi_ru"], "rashi_idx": moon["rashi_idx"]}


def d9_chart(grahas: list[dict], navamsa_lagna_idx: int | None) -> list[dict]:
    """D9 (навамса): раши каждого грахи в навамсе + дом от навамса-лагны."""
    out = []
    for g in grahas:
        nidx = g["navamsa_rashi_idx"]
        out.append({
            "graha": g["graha"],
            "graha_ru": g["graha_ru"],
            "navamsa_rashi": g["navamsa_rashi"],
            "navamsa_rashi_idx": nidx,
            "house": _house_whole_sign(nidx, navamsa_lagna_idx),
        })
    return out
