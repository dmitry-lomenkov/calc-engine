"""Совместимость Ашта-кута (Гуна-милан), максимум 36 баллов.

Стандартный набор из 8 кут. Реализация опирается на классические таблицы; для спорных
кут (Вашья, Йони) используются широко распространённые варианты — помечено в source_note.
Вход: раши-индекс Луны и накшатра-индекс каждого партнёра (A — невеста, B — жених).
"""

from __future__ import annotations

from . import constants as K


def _varna(rashi_idx: int) -> str:
    return K.VARNA_BY_RASHI[rashi_idx]


def varna_kuta(a_rashi: int, b_rashi: int) -> float:
    # балл 1, если варна жениха (B) >= варны невесты (A)
    ra, rb = K.VARNA_RANK[_varna(a_rashi)], K.VARNA_RANK[_varna(b_rashi)]
    return 1.0 if rb >= ra else 0.0


def vashya_kuta(a_rashi: int, b_rashi: int) -> float:
    # 2 — одна группа; 1 — совместимые группы; иначе 0 (упрощённый стандарт)
    ga, gb = K.VASHYA_GROUP[a_rashi], K.VASHYA_GROUP[b_rashi]
    if ga == gb:
        return 2.0
    compatible = {
        frozenset({"Chatushpada", "Vanachar"}): 1.0,
        frozenset({"Manav", "Jalachar"}): 1.0,
        frozenset({"Jalachar", "Keet"}): 1.0,
    }
    return compatible.get(frozenset({ga, gb}), 0.0)


def tara_kuta(a_nak: int, b_nak: int) -> float:
    def score(from_n, to_n):
        cnt = ((to_n - from_n) % 27) + 1
        r = cnt % 9
        # благоприятные остатки: не 3,5,7 (Vipat, Pratyak, Naidhana)
        return 0.0 if r in (3, 5, 7) else 1.5
    return score(a_nak, b_nak) + score(b_nak, a_nak)  # макс 3


_YONI_ENEMIES = {
    frozenset({"Cow", "Tiger"}), frozenset({"Horse", "Buffalo"}),
    frozenset({"Elephant", "Lion"}), frozenset({"Serpent", "Mongoose"}),
    frozenset({"Dog", "Deer"}), frozenset({"Monkey", "Sheep"}),
    frozenset({"Cat", "Rat"}),
}


def yoni_kuta(a_nak: int, b_nak: int) -> float:
    aa, _ = K.YONI[a_nak]
    bb, _ = K.YONI[b_nak]
    if aa == bb:
        return 4.0
    if frozenset({aa, bb}) in _YONI_ENEMIES:
        return 0.0
    return 2.0  # нейтрально (упрощённо)


def graha_maitri_kuta(a_rashi: int, b_rashi: int) -> float:
    la, lb = K.RASHIS[a_rashi]["lord"], K.RASHIS[b_rashi]["lord"]
    if la == lb:
        return 5.0

    def rel(x, y):
        f = K.PLANET_FRIENDS.get(x, {})
        if y in f.get("friends", set()):
            return "friend"
        if y in f.get("enemies", set()):
            return "enemy"
        return "neutral"
    r1, r2 = rel(la, lb), rel(lb, la)
    table = {
        ("friend", "friend"): 5.0, ("friend", "neutral"): 4.0, ("neutral", "friend"): 4.0,
        ("neutral", "neutral"): 3.0, ("friend", "enemy"): 1.0, ("enemy", "friend"): 1.0,
        ("neutral", "enemy"): 0.5, ("enemy", "neutral"): 0.5, ("enemy", "enemy"): 0.0,
    }
    return table.get((r1, r2), 3.0)


def gana_kuta(a_nak: int, b_nak: int) -> float:
    ga, gb = K.GANA[a_nak], K.GANA[b_nak]
    if ga == gb:
        return 6.0
    pair = frozenset({ga, gb})
    if pair == frozenset({"Deva", "Manushya"}):
        return 5.0
    if pair == frozenset({"Manushya", "Rakshasa"}):
        return 1.0
    if pair == frozenset({"Deva", "Rakshasa"}):
        return 0.0
    return 0.0


def bhakoot_kuta(a_rashi: int, b_rashi: int) -> float:
    d1 = ((b_rashi - a_rashi) % 12) + 1
    d2 = ((a_rashi - b_rashi) % 12) + 1
    bad = {(6, 8), (8, 6), (2, 12), (12, 2), (5, 9), (9, 5)}
    return 0.0 if (d1, d2) in bad else 7.0


def nadi_kuta(a_nak: int, b_nak: int) -> float:
    return 0.0 if K.NADI[a_nak] == K.NADI[b_nak] else 8.0


def _lords_friendly(l1: str, l2: str) -> bool:
    if l1 == l2:
        return True
    f = K.PLANET_FRIENDS.get(l1, {})
    return l2 in f.get("friends", set())


def nadi_dosha_cancelled(a_rashi, a_nak, b_rashi, b_nak) -> tuple[bool, str | None]:
    """Правила отмены Нади-доши (нади-парихара), классические:
    1) одна накшатра, но разные раши;
    2) один раши, но разные накшатры;
    3) управители джанма-накшатр — друзья или совпадают."""
    if K.NADI[a_nak] != K.NADI[b_nak]:
        return False, None  # доши нет
    if a_nak == b_nak and a_rashi != b_rashi:
        return True, "одна накшатра, разные раши"
    if a_rashi == b_rashi and a_nak != b_nak:
        return True, "один раши, разные накшатры"
    la = K.VIMSHOTTARI_ORDER[a_nak % 9]
    lb = K.VIMSHOTTARI_ORDER[b_nak % 9]
    if _lords_friendly(la, lb):
        return True, "управители накшатр дружественны/совпадают"
    return False, "нади-доша (одна нади)"


def bhakoot_dosha_cancelled(a_rashi, b_rashi) -> tuple[bool, str | None]:
    """Отмена Бхакут-доши: управители раши совпадают или дружественны."""
    d1 = ((b_rashi - a_rashi) % 12) + 1
    d2 = ((a_rashi - b_rashi) % 12) + 1
    if (d1, d2) not in {(6, 8), (8, 6), (2, 12), (12, 2), (5, 9), (9, 5)}:
        return False, None
    la, lb = K.RASHIS[a_rashi]["lord"], K.RASHIS[b_rashi]["lord"]
    if la == lb or _lords_friendly(la, lb):
        return True, "управители раши совпадают/дружественны"
    return False, "бхакут-доша"


def ashtakuta(a_rashi: int, a_nak: int, b_rashi: int, b_nak: int) -> dict:
    nadi_score = nadi_kuta(a_nak, b_nak)
    bhakoot_score = bhakoot_kuta(a_rashi, b_rashi)
    doshas = []

    # отмена нади-доши
    if nadi_score == 0.0:
        cancelled, reason = nadi_dosha_cancelled(a_rashi, a_nak, b_rashi, b_nak)
        if cancelled:
            nadi_score = 8.0
            doshas.append({"type": "nadi", "present": True, "cancelled": True, "reason": reason})
        else:
            doshas.append({"type": "nadi", "present": True, "cancelled": False, "reason": reason})
    # отмена бхакут-доши
    if bhakoot_score == 0.0:
        cancelled, reason = bhakoot_dosha_cancelled(a_rashi, b_rashi)
        if cancelled:
            bhakoot_score = 7.0
            doshas.append({"type": "bhakoot", "present": True, "cancelled": True, "reason": reason})
        else:
            doshas.append({"type": "bhakoot", "present": True, "cancelled": False, "reason": "несовместимость раши"})

    items = {
        "varna": {"score": varna_kuta(a_rashi, b_rashi), "max": 1},
        "vashya": {"score": vashya_kuta(a_rashi, b_rashi), "max": 2},
        "tara": {"score": tara_kuta(a_nak, b_nak), "max": 3},
        "yoni": {"score": yoni_kuta(a_nak, b_nak), "max": 4},
        "graha_maitri": {"score": graha_maitri_kuta(a_rashi, b_rashi), "max": 5},
        "gana": {"score": gana_kuta(a_nak, b_nak), "max": 6},
        "bhakoot": {"score": bhakoot_score, "max": 7},
        "nadi": {"score": nadi_score, "max": 8},
    }
    total = sum(i["score"] for i in items.values())
    return {
        "kutas": items,
        "total": round(total, 2),
        "max_total": 36,
        "doshas": doshas,
        "verdict": "хорошо" if total >= 18 else "низкая совместимость",
        "dosha_rules_implemented": [
            "Нади-доша: отмена при (одна накшатра+разные раши) / (один раши+разные накшатры) / дружественные управители накшатр",
            "Бхакут-доша: отмена при совпадении или дружбе управителей раши",
        ],
        "not_implemented": ["Мангал (кужа) доша — вне 36 баллов, отдельный модуль (позже)"],
        "source_note": "Ашта-кута (Гуна-милан) по Парашаре; Йони/Вашья — распространённые классические таблицы; "
                       "прямой скрейп калькулятора drikpanchang невозможен (JS-форма) — сверка по опубликованным правилам",
    }
