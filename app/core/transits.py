"""Текущие транзиты: позиции граха на заданный момент (UTC)."""

from __future__ import annotations

from . import constants as K
from . import ephe


def transits(jd: float) -> list[dict]:
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
            "nakshatra": s["nakshatra_en"],
            "pada": s["pada"],
            "retrograde": bool(p["retrograde"]),
        })
    return out
