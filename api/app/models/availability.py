import uuid
from datetime import datetime, timezone

from app.extensions import db, GUID


class ProfessionalAvailability(db.Model):
    __tablename__ = "professional_availability"

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    professional_id = db.Column(
        GUID, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    day_of_week = db.Column(db.Integer, nullable=False)  # 0=Mon, 6=Sun (Python weekday())
    start_time = db.Column(db.String(5), nullable=False)  # "09:00"
    end_time = db.Column(db.String(5), nullable=False)  # "17:00"
    slot_duration_minutes = db.Column(db.Integer, default=30, nullable=False)
    booking_window_days = db.Column(db.Integer, default=30, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    professional = db.relationship("User", foreign_keys=[professional_id])

    __table_args__ = (
        db.Index("ix_professional_availability_prof", "professional_id", "is_active"),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "professional_id": str(self.professional_id),
            "day_of_week": self.day_of_week,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "slot_duration_minutes": self.slot_duration_minutes,
            "booking_window_days": self.booking_window_days,
            "is_active": self.is_active,
        }


class AvailabilityOverride(db.Model):
    __tablename__ = "availability_overrides"

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    professional_id = db.Column(
        GUID, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    override_date = db.Column(db.Date, nullable=False)
    override_type = db.Column(
        db.Enum("block", "extra", name="override_type"),
        nullable=False,
    )
    start_time = db.Column(db.String(5), nullable=True)  # null = full day block
    end_time = db.Column(db.String(5), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    professional = db.relationship("User", foreign_keys=[professional_id])

    __table_args__ = (
        db.Index("ix_availability_overrides_prof_date", "professional_id", "override_date"),
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "professional_id": str(self.professional_id),
            "override_date": self.override_date.isoformat(),
            "override_type": self.override_type,
            "start_time": self.start_time,
            "end_time": self.end_time,
        }
