"""Central configuration for body composition / measurement metrics.

Each metric (body fat, muscle mass, waist, hips, neck) has its own
log table that mirrors `weigh_ins`. The specs below are the single
source of truth for valid ranges, column names, units, and the model
each one binds to. Imported by the CRUD blueprint factory for input
validation and by auth.py to serialize the latest value into the
/auth/me response.
"""
import math
from dataclasses import dataclass
from typing import Type

from app.extensions import db
from app.models.body_metric import (
    BodyFatLog,
    HipsMeasurement,
    MuscleMassLog,
    NeckMeasurement,
    WaistMeasurement,
)


NOTES_MAX_LENGTH = 1000


@dataclass(frozen=True)
class MetricSpec:
    column: str        # SQLAlchemy attribute + JSON key
    model: Type[db.Model]
    min_value: float
    max_value: float
    unit: str          # display hint only ("%", "kg", "cm")


BODY_FAT = MetricSpec("body_fat_pct", BodyFatLog, 3.0, 75.0, "%")
MUSCLE_MASS = MetricSpec("muscle_mass_kg", MuscleMassLog, 10.0, 120.0, "kg")
WAIST = MetricSpec("waist_cm", WaistMeasurement, 40.0, 200.0, "cm")
HIPS = MetricSpec("hips_cm", HipsMeasurement, 50.0, 200.0, "cm")
NECK = MetricSpec("neck_cm", NeckMeasurement, 20.0, 70.0, "cm")

# Canonical ordered registry — iterate this anywhere a "for each metric" loop
# is needed (auth.py stats helper, future bulk endpoints, etc.).
METRICS: tuple[MetricSpec, ...] = (BODY_FAT, MUSCLE_MASS, WAIST, HIPS, NECK)


def validate_value_in_range(raw, spec: MetricSpec):
    """Coerce raw to a finite float within [min, max].

    Returns (value, None) on success, or (None, error_message) on failure.
    Rejects NaN / Infinity (which would otherwise slip past min/max comparisons).
    """
    try:
        value = float(raw)
    except (ValueError, TypeError):
        return None, f"{spec.column} must be a number"
    if not math.isfinite(value):
        return None, f"{spec.column} must be a finite number"
    if value < spec.min_value or value > spec.max_value:
        return (
            None,
            f"{spec.column} must be between {spec.min_value} and {spec.max_value} {spec.unit}",
        )
    return value, None


def clean_notes(raw):
    """Coerce the optional notes field. Returns (value, None) or (None, error)."""
    if raw is None:
        return None, None
    if not isinstance(raw, str):
        return None, "notes must be a string"
    if len(raw) > NOTES_MAX_LENGTH:
        return None, f"notes must be {NOTES_MAX_LENGTH} characters or fewer"
    return raw, None
