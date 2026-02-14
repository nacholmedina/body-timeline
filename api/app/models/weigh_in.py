import uuid
from datetime import datetime, timezone

from app.extensions import db, GUID


class WeighIn(db.Model):
    __tablename__ = "weigh_ins"

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    patient_id = db.Column(
        GUID, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    weight_kg = db.Column(db.Numeric(5, 2), nullable=False)
    recorded_at = db.Column(db.DateTime(timezone=True), nullable=False)
    notes = db.Column(db.Text, nullable=True)
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

    patient = db.relationship("User", back_populates="weigh_ins")

    __table_args__ = (db.Index("ix_weigh_ins_patient_recorded", "patient_id", "recorded_at"),)

    def to_dict(self):
        return {
            "id": str(self.id),
            "patient_id": str(self.patient_id),
            "weight_kg": float(self.weight_kg),
            "recorded_at": self.recorded_at.isoformat(),
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
