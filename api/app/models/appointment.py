import uuid
from datetime import datetime, timezone

from app.extensions import db, GUID


class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    patient_id = db.Column(
        GUID, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    professional_id = db.Column(
        GUID, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    scheduled_at = db.Column(db.DateTime(timezone=True), nullable=False)
    duration_minutes = db.Column(db.Integer, default=30, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.Enum("scheduled", "completed", "cancelled", name="appointment_status"),
        nullable=False,
        default="scheduled",
    )
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

    patient = db.relationship("User", foreign_keys=[patient_id])
    professional = db.relationship("User", foreign_keys=[professional_id])

    __table_args__ = (db.Index("ix_appointments_patient_scheduled", "patient_id", "scheduled_at"),)

    def to_dict(self):
        return {
            "id": str(self.id),
            "patient_id": str(self.patient_id),
            "professional_id": str(self.professional_id),
            "professional_name": (
                f"{self.professional.first_name} {self.professional.last_name}"
                if self.professional else None
            ),
            "scheduled_at": self.scheduled_at.isoformat(),
            "duration_minutes": self.duration_minutes,
            "title": self.title,
            "notes": self.notes,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
