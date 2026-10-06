"""Вимшоттари-даши: маха + антар, с датами. Точка отсчёта — накшатра Луны."""

from __future__ import annotations

from datetime import datetime, timedelta

from . import constants as K
from . import ephe

_YEAR_DAYS = 365.2425  # средний григорианский год


def _add_years(dt: datetime, years: float) -> datetime:
    return dt + timedelta(days=years * _YEAR_DAYS)


def vimshottari(moon_lon: float, birth_utc: datetime, levels: int = 2) -> dict:
    """
    moon_lon — сидерическая долгота Луны (град).
    birth_utc — момент рождения (UTC, naive).
    Возвращает маха-периоды; для каждого — антар-периоды (если levels>=2).
    """
    arcmin = (moon_lon % 360.0) * 60.0
    nak_idx = int(arcmin // 800) % 27
    pos_in_nak = arcmin - nak_idx * 800  # 0..800
    frac_elapsed = pos_in_nak / 800.0

    start_lord_i = nak_idx % 9
    first_lord = K.VIMSHOTTARI_ORDER[start_lord_i]
    first_years = K.VIMSHOTTARI_YEARS[first_lord]
    balance_years = first_years * (1.0 - frac_elapsed)

    # начало текущей махадаши = рождение - истёкшая часть
    maha_start = _add_years(birth_utc, -(first_years * frac_elapsed))

    mahas = []
    cursor = maha_start
    for k in range(9 + 1):  # текущая + 9 следующих (перекрытие цикла)
        lord = K.VIMSHOTTARI_ORDER[(start_lord_i + k) % 9]
        years = K.VIMSHOTTARI_YEARS[lord]
        end = _add_years(cursor, years)
        entry = {
            "lord": lord,
            "lord_ru": K.GRAHA_RU[lord],
            "start": cursor.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
            "years": years,
        }
        if levels >= 2:
            entry["antardashas"] = _antardashas(lord, cursor, years)
        mahas.append(entry)
        cursor = end

    return {
        "moon_nakshatra": K.NAKSHATRAS[nak_idx]["en"],
        "moon_nakshatra_ru": K.NAKSHATRAS[nak_idx]["ru"],
        "starting_lord": first_lord,
        "balance_years_at_birth": round(balance_years, 4),
        "mahadashas": mahas,
    }


def _antardashas(maha_lord: str, maha_start: datetime, maha_years: float) -> list[dict]:
    """Антардаши внутри махадаши: та же последовательность, начиная с самого управителя."""
    order = K.VIMSHOTTARI_ORDER
    start_i = order.index(maha_lord)
    out = []
    cursor = maha_start
    for k in range(9):
        sub = order[(start_i + k) % 9]
        sub_years = maha_years * K.VIMSHOTTARI_YEARS[sub] / K.VIMSHOTTARI_TOTAL
        end = _add_years(cursor, sub_years)
        out.append({
            "lord": sub,
            "lord_ru": K.GRAHA_RU[sub],
            "start": cursor.strftime("%Y-%m-%d"),
            "end": end.strftime("%Y-%m-%d"),
            "years": round(sub_years, 4),
        })
        cursor = end
    return out


def current_dasha(vim: dict, at: datetime) -> dict | None:
    """Активные маха/антар на дату at (UTC)."""
    d = at.strftime("%Y-%m-%d")
    for m in vim["mahadashas"]:
        if m["start"] <= d < m["end"]:
            cur = {"mahadasha": m["lord"], "mahadasha_ru": m["lord_ru"]}
            for a in m.get("antardashas", []):
                if a["start"] <= d < a["end"]:
                    cur["antardasha"] = a["lord"]
                    cur["antardasha_ru"] = a["lord_ru"]
                    break
            return cur
    return None
