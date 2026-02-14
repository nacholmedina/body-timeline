import uuid
from datetime import datetime, timezone

from app.extensions import db, GUID


class Goal(db.Model):
    __tablename__ = "goals"

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    patient_id = db.Column(
        GUID, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    period = db.Column(
        db.Enum("weekly", "monthly", "yearly", name="goal_period"),
        nullable=False,
        default="weekly",
    )
    target_date = db.Column(db.Date, nullable=True)
    is_completed = db.Column(db.Boolean, default=False, nullable=False)
    completed_at = db.Column(db.DateTime(timezone=True), nullable=True)
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

    patient = db.relationship("User", back_populates="goals")

    __table_args__ = (db.Index("ix_goals_patient_period", "patient_id", "period"),)

    def to_dict(self):
        return {
            "id": str(self.id),
            "patient_id": str(self.patient_id),
            "title": self.title,
            "description": self.description,
            "period": self.period,
            "target_date": self.target_date.isoformat() if self.target_date else None,
            "is_completed": self.is_completed,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
