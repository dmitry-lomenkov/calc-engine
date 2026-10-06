"""Конфигурация calc_engine. Настройки детерминированы и попадают в ответ API."""

from __future__ import annotations

import os

ENGINE_VERSION = "0.2.0"

# Пути
EPHE_PATH = os.getenv("EPHE_PATH", os.path.join(os.path.dirname(__file__), "ephe"))

# Сидерические настройки (в ответе — как есть)
AYANAMSHA = os.getenv("AYANAMSHA", "lahiri")          # sidereal mode
HOUSE_SYSTEM = os.getenv("HOUSE_SYSTEM", "whole_sign")
ZODIAC = os.getenv("ZODIAC", "sidereal")
# Узлы: 'mean' (средний, как drikpanchang — подтверждено сверкой) или 'true' (истинный).
NODE_TYPE = os.getenv("NODE_TYPE", "mean")

SETTINGS_DICT = {
    "ayanamsha": AYANAMSHA,
    "house_system": HOUSE_SYSTEM,
    "zodiac": ZODIAC,
    "node_type": NODE_TYPE,
    "ephemeris_range": "1800-2399",
}
