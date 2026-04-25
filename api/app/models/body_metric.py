"""Body composition and measurement log tables.

Each metric is a separate table that mirrors `weigh_ins`: a per-patient,
timestamped log used to support trend charts later. Values are always
stored in metric units (kg, cm, %). Imperial display is metric-only for
v1; the frontend can plug in `unitStore`-driven conversions (see the
`formatHeight` / `formatWeight` precedents) without schema changes.
"""
import uuid
from datetime import datetime, timezone

from app.extensions import db, GUID


def _ts_default():
    return datetime.now(timezone.utc)


class _BodyMetricMixin:
    """Shared columns + serialization for all body-metric log models."""

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    recorded_at = db.Column(db.DateTime(timezone=True), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), default=_ts_default, nullable=False)
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=_ts_default,
        onupdate=_ts_default,
        nullable=False,
    )

    # Subclasses must define: __tablename__, patient_id (FK), the value column,
    # `patient` relationship, and override `_value_field` for serialization.
    _value_field: str = ""

    def to_dict(self):
        value = getattr(self, self._value_field)
        return {
            "id": str(self.id),
            "patient_id": str(self.patient_id),
            self._value_field: float(value) if value is not None else None,
            "recorded_at": self.recorded_at.isoformat(),
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class BodyFatLog(_BodyMetricMixin, db.Model):
    __tablename__ = "body_fat_logs"
    _value_field = "body_fat_pct"

    patient_id = db.Column(
        GUID, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    body_fat_pct = db.Column(db.Numeric(4, 1), nullable=False)
    patient = db.relationship("User", back_populates="body_fat_logs")

    __table_args__ = (
        db.Index("ix_body_fat_logs_patient_recorded", "patient_id", "recorded_at"),
    )


class MuscleMassLog(_BodyMetricMixin, db.Model):
    __tablename__ = "muscle_mass_logs"
    _value_field = "muscle_mass_kg"

    patient_id = db.Column(
        GUID, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    muscle_mass_kg = db.Column(db.Numeric(5, 2), nullable=False)
    patient = db.relationship("User", back_populates="muscle_mass_logs")

    __table_args__ = (
        db.Index("ix_muscle_mass_logs_patient_recorded", "patient_id", "recorded_at"),
    )


class WaistMeasurement(_BodyMetricMixin, db.Model):
    __tablename__ = "waist_measurements"
    _value_field = "waist_cm"

    patient_id = db.Column(
        GUID, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    waist_cm = db.Column(db.Numeric(5, 1), nullable=False)
    patient = db.relationship("User", back_populates="waist_measurements")

    __table_args__ = (
        db.Index("ix_waist_measurements_patient_recorded", "patient_id", "recorded_at"),
    )


class HipsMeasurement(_BodyMetricMixin, db.Model):
    __tablename__ = "hips_measurements"
    _value_field = "hips_cm"

    patient_id = db.Column(
        GUID, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    hips_cm = db.Column(db.Numeric(5, 1), nullable=False)
    patient = db.relationship("User", back_populates="hips_measurements")

    __table_args__ = (
        db.Index("ix_hips_measurements_patient_recorded", "patient_id", "recorded_at"),
    )


class NeckMeasurement(_BodyMetricMixin, db.Model):
    __tablename__ = "neck_measurements"
    _value_field = "neck_cm"

    patient_id = db.Column(
        GUID, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    neck_cm = db.Column(db.Numeric(4, 1), nullable=False)
    patient = db.relationship("User", back_populates="neck_measurements")

    __table_args__ = (
        db.Index("ix_neck_measurements_patient_recorded", "patient_id", "recorded_at"),
    )
