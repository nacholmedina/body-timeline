import uuid
from datetime import datetime, timezone

from app.extensions import db, GUID


class Exercise(db.Model):
    __tablename__ = "exercises"

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(200), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    exercise_type = db.Column(
        db.Enum("duration", "sets_reps", "both", name="exercise_type"),
        nullable=False,
        default="sets_reps",
    )
    muscle_group = db.Column(db.String(100), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    def to_dict(self):
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "exercise_type": self.exercise_type,
            "muscle_group": self.muscle_group,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }


class ExerciseRequest(db.Model):
    __tablename__ = "exercise_requests"

    id = db.Column(GUID, primary_key=True, default=uuid.uuid4)
    requested_by = db.Column(
        GUID, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    exercise_type = db.Column(
        db.Enum("duration", "sets_reps", "both", name="exercise_type", create_type=False),
        nullable=False,
        default="sets_reps",
    )
    status = db.Column(
        db.Enum("pending", "approved", "rejected", name="request_status"),
        nullable=False,
        default="pending",
    )
    reviewed_by = db.Column(GUID, db.ForeignKey("users.id"), nullable=True)
    reviewed_at = db.Column(db.DateTime(timezone=True), nullable=True)
    created_exercise_id = db.Column(GUID, db.ForeignKey("exercises.id"), nullable=True)
    created_at = db.Column(
        db.DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    requester = db.relationship("User", foreign_keys=[requested_by])
    reviewer = db.relationship("User", foreign_keys=[reviewed_by])
    created_exercise = db.relationship("Exercise", foreign_keys=[created_exercise_id])

    def to_dict(self):
        return {
            "id": str(self.id),
            "requested_by": str(self.requested_by),
            "name": self.name,
            "description": self.description,
            "exercise_type": self.exercise_type,
            "status": self.status,
            "reviewed_by": str(self.reviewed_by) if self.reviewed_by else None,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else None,
            "created_exercise_id": str(self.created_exercise_id) if self.created_exercise_id else None,
            "created_at": self.created_at.isoformat(),
        }
