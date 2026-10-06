"""Персональный день: тара-бала, чандраштама, накшатра и титхи дня.

Тара-бала — благоприятность дня по счёту от натальной накшатры Луны до накшатры дня (9 тар,
цикл повторяется 3 раза по 27). Чандраштама — Луна дня в 8-м знаке от натальной Луны (сложный день).
"""

from __future__ import annotations

from datetime import datetime

from . import constants as K
from . import ephe

# 9 тар: имя, благоприятность
TARA = [
    ("Джанма", "своя — осторожность", False),
    ("Сампат", "богатство — благоприятно", True),
    ("Випат", "препятствия — неблагоприятно", False),
    ("Кшема", "благополучие — благоприятно", True),
    ("Пратьяк", "помехи — неблагоприятно", False),
    ("Садхака", "достижения — благоприятно", True),
    ("Вадха", "препятствие — неблагоприятно", False),
    ("Митра", "друг — благоприятно", True),
    ("Ати-митра", "лучший друг — благоприятно", True),
]


def tara_bala(natal_nak_idx: int, day_nak_idx: int) -> dict:
    count = ((day_nak_idx - natal_nak_idx) % 27) + 1  # 1..27
    tara_idx = (count - 1) % 9
    name, meaning, good = TARA[tara_idx]
    cycle = (count - 1) // 9 + 1  # 1..3
    return {"number": tara_idx + 1, "name": name, "meaning": meaning,
            "favorable": good, "count_from_natal": count, "cycle": cycle}


def chandrashtama(natal_moon_rashi_idx: int, day_moon_rashi_idx: int) -> dict:
    dist = ((day_moon_rashi_idx - natal_moon_rashi_idx) % 12) + 1
    is_ca = dist == 8
    return {"is_chandrashtama": is_ca, "moon_house_from_natal": dist,
            "note": "Чандраштама: Луна в 8-м от натальной — день повышенной чувствительности, "
                    "лучше без важных начинаний" if is_ca else "не чандраштама"}


def personal_day(natal_moon_lon: float, jd_day: float) -> dict:
    natal = ephe.split_longitude(natal_moon_lon)
    day_moon_lon = ephe.sun_moon_lon(jd_day)[1]
    day = ephe.split_longitude(day_moon_lon)
    tb = tara_bala(natal["nakshatra_idx"], day["nakshatra_idx"])
    ca = chandrashtama(natal["rashi_idx"], day["rashi_idx"])
    # титхи дня
    sun, moon = ephe.sun_moon_lon(jd_day)
    diff = (moon - sun) % 360.0
    tithi_idx = int(diff // 12)
    paksha = "Shukla" if tithi_idx < 15 else "Krishna"
    within = tithi_idx % 15
    tname = ("Пурнима" if paksha == "Shukla" else "Амавасья") if within == 14 else K.TITHI_NAMES[within]
    return {
        "natal_moon": {"nakshatra": natal["nakshatra_en"], "rashi": natal["rashi_en"]},
        "day_moon": {"nakshatra": day["nakshatra_en"], "nakshatra_ru": day["nakshatra_ru"],
                     "rashi": day["rashi_en"], "pada": day["pada"]},
        "tara_bala": tb,
        "chandrashtama": ca,
        "day_tithi": {"index": tithi_idx + 1, "name": tname, "paksha": paksha},
    }
