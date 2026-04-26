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


def _find_metric_entry(spec: MetricSpec, patient_id, recorded_at):
    return spec.model.query.filter_by(
        patient_id=patient_id, recorded_at=recorded_at
    ).first()


def apply_body_metrics(patient_id, payload, new_recorded_at, old_recorded_at=None):
    """Sync body-metric rows alongside a weigh-in within the current session.

    payload: dict mapping a metric's column → number | None.
        - number  → upsert the metric at new_recorded_at
        - None    → delete the existing entry (if any) at old_recorded_at
        - absent  → leave alone, but follow the weigh-in's recorded_at if it changed

    Returns (error_message, field_column) on validation failure (caller should
    rollback), or (None, None) on success (caller should commit).
    """
    if old_recorded_at is None:
        old_recorded_at = new_recorded_at
    moved = old_recorded_at != new_recorded_at

    for spec in METRICS:
        if spec.column not in payload:
            if moved:
                existing = _find_metric_entry(spec, patient_id, old_recorded_at)
                if existing:
                    existing.recorded_at = new_recorded_at
            continue

        raw = payload[spec.column]
        existing = _find_metric_entry(spec, patient_id, old_recorded_at)

        if raw is None:
            if existing:
                db.session.delete(existing)
            continue

        value, err = validate_value_in_range(raw, spec)
        if err:
            return err, spec.column

        if existing:
            setattr(existing, spec.column, value)
            if moved:
                existing.recorded_at = new_recorded_at
        else:
            entry = spec.model(
                patient_id=patient_id,
                recorded_at=new_recorded_at,
            )
            setattr(entry, spec.column, value)
            db.session.add(entry)

    return None, None


def serialize_body_metrics(patient_id, recorded_at):
    """Return {column → entry.to_dict() | None} for the metrics linked to a weigh-in."""
    out = {}
    for spec in METRICS:
        entry = _find_metric_entry(spec, patient_id, recorded_at)
        out[spec.column] = entry.to_dict() if entry else None
    return out
