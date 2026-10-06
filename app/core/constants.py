"""Справочные константы для расчётов (имена, управители, таблицы кут).

Только то, что нужно ДВИЖКУ для вычислений. Содержательные тексты интерпретаций
(мифы, качества и т.п.) живут в knowledge_base, не здесь.
"""

from __future__ import annotations

# ── 12 раши (знаков), 0 = Овен. Управители — для граха-майтри и т.п. ──
RASHIS = [
    {"idx": 0,  "en": "Aries",       "ru": "Овен",       "lord": "Mars"},
    {"idx": 1,  "en": "Taurus",      "ru": "Телец",      "lord": "Venus"},
    {"idx": 2,  "en": "Gemini",      "ru": "Близнецы",   "lord": "Mercury"},
    {"idx": 3,  "en": "Cancer",      "ru": "Рак",        "lord": "Moon"},
    {"idx": 4,  "en": "Leo",         "ru": "Лев",        "lord": "Sun"},
    {"idx": 5,  "en": "Virgo",       "ru": "Дева",       "lord": "Mercury"},
    {"idx": 6,  "en": "Libra",       "ru": "Весы",       "lord": "Venus"},
    {"idx": 7,  "en": "Scorpio",     "ru": "Скорпион",   "lord": "Mars"},
    {"idx": 8,  "en": "Sagittarius", "ru": "Стрелец",    "lord": "Jupiter"},
    {"idx": 9,  "en": "Capricorn",   "ru": "Козерог",    "lord": "Saturn"},
    {"idx": 10, "en": "Aquarius",    "ru": "Водолей",    "lord": "Saturn"},
    {"idx": 11, "en": "Pisces",      "ru": "Рыбы",       "lord": "Jupiter"},
]

# ── 27 накшатр, 0 = Ашвини. Управитель по Вимшоттари = index % 9. ──
NAKSHATRAS = [
    {"idx": 0,  "en": "Ashwini",          "ru": "Ашвини"},
    {"idx": 1,  "en": "Bharani",          "ru": "Бхарани"},
    {"idx": 2,  "en": "Krittika",         "ru": "Криттика"},
    {"idx": 3,  "en": "Rohini",           "ru": "Рохини"},
    {"idx": 4,  "en": "Mrigashira",       "ru": "Мригашира"},
    {"idx": 5,  "en": "Ardra",            "ru": "Ардра"},
    {"idx": 6,  "en": "Punarvasu",        "ru": "Пунарвасу"},
    {"idx": 7,  "en": "Pushya",           "ru": "Пушья"},
    {"idx": 8,  "en": "Ashlesha",         "ru": "Ашлеша"},
    {"idx": 9,  "en": "Magha",            "ru": "Магха"},
    {"idx": 10, "en": "Purva Phalguni",   "ru": "Пурва Пхалгуни"},
    {"idx": 11, "en": "Uttara Phalguni",  "ru": "Уттара Пхалгуни"},
    {"idx": 12, "en": "Hasta",            "ru": "Хаста"},
    {"idx": 13, "en": "Chitra",           "ru": "Читра"},
    {"idx": 14, "en": "Swati",            "ru": "Свати"},
    {"idx": 15, "en": "Vishakha",         "ru": "Вишакха"},
    {"idx": 16, "en": "Anuradha",         "ru": "Анурадха"},
    {"idx": 17, "en": "Jyeshtha",         "ru": "Джьештха"},
    {"idx": 18, "en": "Mula",             "ru": "Мула"},
    {"idx": 19, "en": "Purva Ashadha",    "ru": "Пурва Ашадха"},
    {"idx": 20, "en": "Uttara Ashadha",   "ru": "Уттара Ашадха"},
    {"idx": 21, "en": "Shravana",         "ru": "Шравана"},
    {"idx": 22, "en": "Dhanishta",        "ru": "Дхаништха"},
    {"idx": 23, "en": "Shatabhisha",      "ru": "Шатабхиша"},
    {"idx": 24, "en": "Purva Bhadrapada", "ru": "Пурва Бхадрапада"},
    {"idx": 25, "en": "Uttara Bhadrapada","ru": "Уттара Бхадрапада"},
    {"idx": 26, "en": "Revati",           "ru": "Ревати"},
]

# ── Вимшоттари: последовательность управителей и длительности (лет) ──
VIMSHOTTARI_ORDER = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
VIMSHOTTARI_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
VIMSHOTTARI_TOTAL = 120

# ── Грахи (9). Ключи — для swisseph (кроме Ketu, считается от Rahu). ──
GRAHA_RU = {
    "Sun": "Солнце", "Moon": "Луна", "Mars": "Марс", "Mercury": "Меркурий",
    "Jupiter": "Юпитер", "Venus": "Венера", "Saturn": "Сатурн",
    "Rahu": "Раху", "Ketu": "Кету",
}

# ── Панчанга: имена ──
TITHI_NAMES = [
    "Пратипада", "Двития", "Трития", "Чатуртхи", "Панчами", "Шаштхи", "Саптами",
    "Аштами", "Навами", "Дашами", "Экадаши", "Двадаши", "Трайодаши", "Чатурдаши",
]  # +Пурнима/Амавасья на 15-х
YOGA_NAMES = [
    "Вишкамбха", "Прити", "Аюшман", "Саубхагья", "Шобхана", "Атиганда", "Сукарма",
    "Дхрити", "Шула", "Ганда", "Вриддхи", "Дхрува", "Вьягхата", "Харшана", "Ваджра",
    "Сиддхи", "Вьятипата", "Вариян", "Паригха", "Шива", "Сиддха", "Садхья", "Шубха",
    "Шукла", "Брахма", "Индра", "Вайдхрити",
]
KARANA_NAMES_MOVABLE = ["Бава", "Балава", "Каулава", "Тайтила", "Гара", "Ваниджа", "Вишти"]
KARANA_NAMES_FIXED = ["Шакуни", "Чатушпада", "Нага", "Кимстугхна"]
VARA_NAMES = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
# индекс vara: 0=Вс в swe.day_of_week? Собственный расчёт в panchanga.

# ── Ашта-кута (совместимость, макс 36) ──
# Варна по раши (водные→Брахман и т.д.). Порядок по знакам 0..11.
VARNA_BY_RASHI = ["Kshatriya", "Vaishya", "Shudra", "Brahmin", "Kshatriya", "Vaishya",
                  "Shudra", "Brahmin", "Kshatriya", "Vaishya", "Shudra", "Brahmin"]
VARNA_RANK = {"Brahmin": 4, "Kshatriya": 3, "Vaishya": 2, "Shudra": 1}

# Вашья: группа по раши
VASHYA_GROUP = ["Chatushpada", "Chatushpada", "Manav", "Jalachar", "Vanachar", "Manav",
                "Manav", "Keet", "Manav", "Jalachar", "Manav", "Jalachar"]
# Луна(Рак)=Jalachar, Козерог первая половина Chatushpada/вторая Jalachar — упрощаем до Jalachar.

# Йони по накшатрам (27) — животное и пол
YONI = [
    ("Horse", "M"), ("Elephant", "M"), ("Sheep", "F"), ("Serpent", "M"), ("Serpent", "F"),
    ("Dog", "F"), ("Cat", "F"), ("Sheep", "M"), ("Cat", "M"), ("Rat", "M"),
    ("Rat", "F"), ("Cow", "F"), ("Buffalo", "F"), ("Tiger", "F"), ("Buffalo", "M"),
    ("Tiger", "M"), ("Deer", "M"), ("Deer", "F"), ("Dog", "M"), ("Monkey", "M"),
    ("Mongoose", "M"), ("Monkey", "F"), ("Lion", "F"), ("Horse", "F"), ("Lion", "M"),
    ("Cow", "M"), ("Elephant", "F"),
]
# Гана по накшатрам (Deva/Manushya/Rakshasa)
GANA = [
    "Deva", "Manushya", "Rakshasa", "Manushya", "Deva", "Manushya", "Deva", "Deva",
    "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva", "Rakshasa", "Deva",
    "Rakshasa", "Deva", "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva",
    "Rakshasa", "Rakshasa", "Manushya", "Manushya", "Deva",
]
# Нади по накшатрам (Adi/Madhya/Antya)
NADI = [
    "Adi", "Madhya", "Antya", "Adi", "Madhya", "Antya", "Adi", "Madhya", "Antya",
    "Adi", "Madhya", "Antya", "Adi", "Madhya", "Antya", "Adi", "Madhya", "Antya",
    "Adi", "Madhya", "Antya", "Adi", "Madhya", "Antya", "Adi", "Madhya", "Antya",
]

# Друзья/враги для граха-майтри (натуральные отношения) — по управителям раши
PLANET_FRIENDS = {
    "Sun": {"friends": {"Moon", "Mars", "Jupiter"}, "enemies": {"Venus", "Saturn"}},
    "Moon": {"friends": {"Sun", "Mercury"}, "enemies": set()},
    "Mars": {"friends": {"Sun", "Moon", "Jupiter"}, "enemies": {"Mercury"}},
    "Mercury": {"friends": {"Sun", "Venus"}, "enemies": {"Moon"}},
    "Jupiter": {"friends": {"Sun", "Moon", "Mars"}, "enemies": {"Mercury", "Venus"}},
    "Venus": {"friends": {"Mercury", "Saturn"}, "enemies": {"Sun", "Moon"}},
    "Saturn": {"friends": {"Mercury", "Venus"}, "enemies": {"Sun", "Moon", "Mars"}},
}
