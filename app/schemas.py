"""Строгие JSON-схемы входа/выхода (pydantic v2)."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, model_validator


class BirthInput(BaseModel):
    date: str = Field(..., description="Дата рождения YYYY-MM-DD", examples=["1985-06-15"])
    time: Optional[str] = Field(None, description="Местное время HH:MM[:SS]", examples=["14:30"])
    time_precision: Literal["exact", "approximate", "unknown"] = "exact"
    approximate_period: Optional[Literal["morning", "day", "evening", "night"]] = None
    place: Optional[str] = Field(None, examples=["Новосибирск"])
    lat: Optional[float] = None
    lon: Optional[float] = None
    geoname_id: Optional[int] = Field(None, description="Точный выбор места из GeoNames (после уточнения)")
    tz_name: Optional[str] = Field(None, description="IANA пояс; обычно определяется автоматически")
    dasha_levels: int = Field(2, ge=1, le=2)

    @model_validator(mode="after")
    def _check(self):
        if self.time_precision == "exact" and not self.time:
            # нет времени → трактуем как unknown, а не ошибка
            object.__setattr__(self, "time_precision", "unknown")
        if self.time_precision == "approximate" and not self.approximate_period:
            object.__setattr__(self, "approximate_period", "day")
        if not self.place and self.geoname_id is None and (self.lat is None or self.lon is None):
            raise ValueError("укажите place, geoname_id или пару lat/lon")
        return self


class TransitInput(BaseModel):
    datetime_utc: str = Field(..., description="Момент UTC YYYY-MM-DD HH:MM[:SS]",
                              examples=["2026-09-27 12:00:00"])


class PanchangaInput(BaseModel):
    date: str
    time: str = Field("12:00", description="Местное время (для точного восхода/титхи)")
    place: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    geoname_id: Optional[int] = None
    tz_name: Optional[str] = None
    at_sunrise: bool = Field(False, description="Считать титхи/накшатру/йогу на момент восхода (панчанга дня)")

    @model_validator(mode="after")
    def _check(self):
        if not self.place and self.geoname_id is None and (self.lat is None or self.lon is None):
            raise ValueError("укажите place, geoname_id или пару lat/lon")
        return self


class SkySequenceInput(BaseModel):
    datetime_utc: Optional[str] = Field(None, description="UTC YYYY-MM-DD[ HH:MM]; по умолчанию — сейчас")
    hours: Optional[float] = Field(48.0, description="окно последовательности переходов, часов")


class SkyEventsInput(BaseModel):
    datetime_utc: Optional[str] = Field(None, description="UTC; по умолчанию — сейчас")
    days: Optional[int] = Field(30, description="горизонт событий, дней")


class GeocodeInput(BaseModel):
    place: Optional[str] = Field(None, examples=["Бердск"])
    lat: Optional[float] = None
    lon: Optional[float] = None
    geoname_id: Optional[int] = None
    tz_name: Optional[str] = None

    @model_validator(mode="after")
    def _check(self):
        if not self.place and self.geoname_id is None and (self.lat is None or self.lon is None):
            raise ValueError("укажите place, geoname_id или пару lat/lon")
        return self


class CompatInput(BaseModel):
    person_a: BirthInput = Field(..., description="Партнёр A (невеста)")
    person_b: BirthInput = Field(..., description="Партнёр B (жених)")


class PersonalDayInput(BaseModel):
    birth: BirthInput = Field(..., description="Данные рождения (для натальной Луны)")
    day: str = Field(..., description="Дата дня для оценки YYYY-MM-DD", examples=["2026-09-28"])


class Meta(BaseModel):
    engine_version: str
    settings: dict
